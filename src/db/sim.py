import time
from typing import List, Tuple, Set, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

import db
from mod import models
from mod.models import IFnProg
from util import log

lg = log.get(__name__)

def normalizeDate(dt) -> str:
    if not dt: return ''
    try:
        # Check if it's a datetime object (has microsecond attribute)
        if hasattr(dt, 'microsecond'):
            return str(dt.replace(microsecond=0))
        else:
            dtStr = str(dt)
            if '.' in dtStr and ('+' in dtStr or dtStr.endswith('Z')):
                beforeDot = dtStr.split('.')[0]
                if '+' in dtStr:
                    timezone = '+' + dtStr.split('+')[-1]
                    return beforeDot + timezone
                elif dtStr.endswith('Z'):
                    return beforeDot + 'Z'
            return dtStr
    except Exception as e:
        return str(dt) if dt else ''

@dataclass
class SearchInfo:
    asset: Optional[models.Asset] = None
    bseVec: List[float] = field(default_factory=list)
    bseInfos: List[models.SimInfo] = field(default_factory=list)
    simAids: List[int] = field(default_factory=list)
    foundSimilar: bool = False
    hasVector: bool = False


@dataclass
class GroupSearchInfo:
    allGroupAssets: List[models.Asset] = field(default_factory=list)
    groupCount: int = 0
    maxGroups: int = 1


class ScoreType(Enum):
    EARLIER = "Earlier"
    LATER = "Later"
    EXIF_RICH = "ExifRich"
    EXIF_POOR = "ExifPoor"
    BIG_SIZE = "BigSize"
    SMALL_SIZE = "SmallSize"
    BIG_DIM = "BigDim"
    SMALL_DIM = "SmallDim"
    LONG_NAME = "LongName"
    SHORT_NAME = "ShortName"


@dataclass
class AssetMetrics:
    aid: int
    dt: str
    exfCnt: int
    fileSz: int
    dim: int
    nameLen: int


def createReporter(doReport: IFnProg) -> Callable[[str], Tuple[int, int]]:
    def autoReport(msg: str) -> Tuple[int, int]:
        cntAll = db.pics.count()
        cntOk = db.pics.countSimOk(1)
        progress = round(cntOk / cntAll * 100, 2) if cntAll > 0 else 0
        doReport(progress, msg)
        return cntOk, cntAll
    return autoReport


def checkGroupConds(assets: List[models.Asset]) -> bool:
    if not assets or len(assets) < 2: return False
    if not db.dto.simCondGrpMode: return True

    doDate = db.dto.simCondSameDate
    doWidth = db.dto.simCondSameWidth
    doHeight = db.dto.simCondSameHeight
    doSize = db.dto.simCondSameSize

    if not any([doDate, doWidth, doHeight, doSize]): return True

    baseAsset = assets[0]
    baseExif = baseAsset.jsonExif
    if not baseExif: return False

    for asset in assets[1:]:
        exif = asset.jsonExif
        if not exif: return False

        if doDate:
            baseDate = str(baseAsset.fileCreatedAt)[:10] if baseAsset.fileCreatedAt else ''
            assetDate = str(asset.fileCreatedAt)[:10] if asset.fileCreatedAt else ''
            if baseDate != assetDate: return False

        if doWidth:
            if baseExif.exifImageWidth != exif.exifImageWidth: return False

        if doHeight:
            if baseExif.exifImageHeight != exif.exifImageHeight: return False

        if doSize:
            if baseExif.fileSizeInByte != exif.fileSizeInByte: return False

    return True


def findCandidate(autoId: int, taskArgs: dict) -> models.Asset:
    asset = None

    if not autoId and taskArgs.get('assetId'):
        lg.info(f"[sim:fnd] search from task args assetId")
        assetId = taskArgs.get('assetId')
        asset = db.pics.getById(assetId)
        if asset: autoId = asset.autoId
    else:
        asset = db.pics.getByAutoId(autoId) if autoId else None

    if not autoId:
        raise RuntimeError(f"[tsk] sim.assAid is empty")

    if not asset:
        raise RuntimeError(f"[sim:fnd] not found asset #{autoId}")

    if asset.simGIDs:
        raise RuntimeError(f"[sim:fnd] asset #{asset.autoId} already searched, please clear All Records first")

    return asset


def search(
    ass: models.Asset, thMin: float, thMax: float,
    autoReport: Callable[[str], Tuple[int, int]],
    isFromUrl: bool, doReport: IFnProg
) -> SearchInfo:
    rst = SearchInfo()
    rst.asset = ass
    cntFnd = 0

    while True:
        if cntFnd <= 0:
            msg = f"[sim:fnd] search #{ass.autoId}, thresholds[{thMin:.2f}-{thMax:.2f}]"
            doReport(10, msg)

        time.sleep(0.1)
        cntFnd += 1

        #todo: 要把bseInfos裡面已經simOk的濾掉

        # Search for similar assets
        bseVec, bseInfos = db.vecs.findSimiliar(ass.autoId, thMin, thMax)
        rst.bseVec = bseVec
        rst.bseInfos = bseInfos

        # Check if vector exists
        if not bseInfos:
            lg.warn(f"[sim:fnd] asset #{ass.autoId} not found any similar, may not store vector")
            db.pics.setVectoredBy(ass, 0)
            rst.hasVector = False

            if isFromUrl:
                msg = f"[sim:fnd] Asset #{ass.autoId} has no vector stored"
                doReport(100, msg)
                return rst

            # Try find next asset
            nextAss = db.pics.getAnyNonSim()
            if not nextAss:
                msg = f"[sim:fnd] No more images to continue searching"
                doReport(100, msg)
                return rst

            lg.info(f"[sim:fnd] No vector for #{ass.autoId}, next: #{nextAss.autoId}")
            autoReport(f"No vector for #{ass.autoId}, continuing to #{nextAss.autoId}...")

            ass = nextAss
            rst.asset = ass
            continue

        rst.hasVector = True
        simAids = [i.aid for i in bseInfos if not i.isSelf]
        rst.simAids = simAids

        # Check if only contains self
        if not simAids:
            lg.info(f"[sim:fnd] NoFound #{ass.autoId}")
            db.pics.setSimInfos(ass.autoId, bseInfos, isOk=1)
            rst.foundSimilar = False

            if isFromUrl:
                msg = f"[sim:fnd] Asset #{ass.autoId} no similar found"
                doReport(100, msg)
                return rst

            # Try find next asset
            nextAss = db.pics.getAnyNonSim()
            if not nextAss:
                msg = f"[sim:fnd] No more images to continue searching"
                doReport(100, msg)
                return rst

            lg.info(f"[sim:fnd] Next: #{nextAss.autoId}")
            autoReport(f"No similar found for #{ass.autoId}, continuing to #{nextAss.autoId}...")
            ass = nextAss
            rst.asset = ass
            continue

        # Found similar assets, check group conditions if enabled
        if db.dto.simCondGrpMode:
            similarAssets = [ass] + [db.pics.getByAutoId(aid) for aid in simAids if db.pics.getByAutoId(aid)]

            if not checkGroupConds(similarAssets):
                lg.info(f"[sim:fnd] Group conditions not met for #{ass.autoId}, marking as resolved and continuing")
                db.pics.setSimInfos(ass.autoId, bseInfos, isOk=1)

                if not isFromUrl:
                    nextAss = db.pics.getAnyNonSim()
                    if not nextAss:
                        msg = f"[sim:fnd] No more images to continue searching"
                        doReport(100, msg)
                        return rst

                    lg.info(f"[sim:fnd] Continuing to next: #{nextAss.autoId}")
                    autoReport(f"Group conditions not met for #{ass.autoId}, continuing to #{nextAss.autoId}...")
                    ass = nextAss
                    rst.asset = ass
                    continue
                else:
                    msg = f"[sim:fnd] Asset #{ass.autoId} group conditions not met"
                    doReport(100, msg)
                    return rst

        # Group conditions met or not in group mode, found similar assets
        rst.foundSimilar = True
        break

    return rst


def processChildren(
    asset: models.Asset, bseInfos: List[models.SimInfo], simAids: List[int],
    thMin: float, thMax: float, maxDepth: int, maxItems: int, doReport: IFnProg
) -> Set[int]:

    rootGID = asset.autoId
    db.pics.setSimGIDs(asset.autoId, rootGID)
    db.pics.setSimInfos(asset.autoId, bseInfos)

    doneIds = {asset.autoId}
    simQ = [(aid, 0) for aid in simAids]

    while simQ:
        aid, depth = simQ.pop(0)
        if aid in doneIds: continue

        doneIds.add(aid)
        doReport(50, f"Processing children similar photo #{aid} depth({depth}) count({len(doneIds)})")

        try:
            ass = db.pics.getByAutoId(aid)
            if ass.simOk: continue  # ignore already resolved

            lg.info(f"[sim:fnd] search child #{aid} depth[{depth}] mx({maxDepth}) items({len(doneIds)}/{maxItems})")
            cVec, cInfos = db.vecs.findSimiliar(aid, thMin, thMax)

            db.pics.setSimGIDs(aid, rootGID)
            db.pics.setSimInfos(aid, cInfos)

            # Add children to queue if haven't reached max depth/items
            if depth < maxDepth and len(doneIds) < maxItems:
                for inf in cInfos:
                    if inf.aid not in doneIds: simQ.append((inf.aid, depth + 1))

        except Exception as ce:
            raise RuntimeError(f"Error processing similar image {aid}: {ce}")

        # Check item limit
        if len(doneIds) >= maxItems:
            lg.warn(f"[sim:fnd] Reached max items limit ({maxItems}), stopping search..")
            doReport(90, f"Reached max items limit ({maxItems}), processing current item...")
            break

    return doneIds


def processCondGroup(asset: models.Asset, grpId: int) -> List[models.Asset]:
    groupAssets = db.pics.getSimAssets(asset.autoId, False) # cond group ignore simIncRelGrp

    for i, ass in enumerate(groupAssets):
        ass.view.condGrpId = grpId
        ass.view.isMain = (i == 0)

    lg.info(f"[sim:fnd] Found group {grpId} with {len(groupAssets)} assets")
    return groupAssets


def searchCondGroups( currentAssets: List[models.Asset], maxGroups: int, thMin: float, thMax: float, maxDepth: int, maxItems: int, doReport: IFnProg) -> GroupSearchInfo:
    result = GroupSearchInfo()
    result.allGroupAssets = currentAssets[:]
    result.groupCount = 1
    result.maxGroups = maxGroups

    if not db.dto.simCondGrpMode or result.groupCount >= maxGroups:
        return result

    doReport(80, f"Searching for additional groups ({result.groupCount}/{maxGroups})...")

    while result.groupCount < maxGroups:
        nextAss = db.pics.getAnyNonSim()
        if not nextAss:
            lg.info(f"[sim:fnd] No more assets to search for additional groups")
            break

        try:
            # Quick similarity search for next group
            doReport(85, f"Checking group {result.groupCount + 1} candidate #{nextAss.autoId}...")
            nextVec, nextInfos = db.vecs.findSimiliar(nextAss.autoId, thMin, thMax)

            if not nextInfos:
                db.pics.setVectoredBy(nextAss, 0)
                continue

            nextSimAids = [i.aid for i in nextInfos if not i.isSelf]
            if not nextSimAids:
                db.pics.setSimInfos(nextAss.autoId, nextInfos, isOk=1)
                continue

            # Check group conditions
            nextSimilarAssets = [nextAss] + [db.pics.getByAutoId(aid) for aid in nextSimAids if db.pics.getByAutoId(aid)]
            if not checkGroupConds(nextSimilarAssets):
                db.pics.setSimInfos(nextAss.autoId, nextInfos, isOk=1)
                continue

            # Found valid group, process it
            result.groupCount += 1
            nextRootGID = nextAss.autoId
            db.pics.setSimGIDs(nextAss.autoId, nextRootGID)
            db.pics.setSimInfos(nextAss.autoId, nextInfos)

            # Process children for this group
            processChildren(nextAss, nextInfos, nextSimAids, thMin, thMax, maxDepth, maxItems, doReport)

            # Add this group's assets
            groupAssets = processCondGroup(nextAss, result.groupCount)
            result.allGroupAssets.extend(groupAssets)

        except Exception as e:
            lg.warn(f"Error searching for group {result.groupCount + 1}: {e}")
            continue

    return result


def getAutoSelectAuids(assets: List[models.Asset]) -> List[int]:
    lg.info(f"[autoSel] Starting auto-selection, auSelEnable[{db.dto.auSelEnable}], assets count={len(assets) if assets else 0}")
    lg.info(f"[autoSel] Weights: Earlier={db.dto.auSel_Earlier}, Later={db.dto.auSel_Later}, ExifRich={db.dto.auSel_ExifRicher}, ExifPoor={db.dto.auSel_ExifPoorer}, BigSize={db.dto.auSel_BiggerSize}, SmallSize={db.dto.auSel_SmallerSize}, BigDim={db.dto.auSel_BiggerDimensions}, SmallDim={db.dto.auSel_SmallerDimensions}, HighSim={db.dto.auSel_SkipLowSim}, AlwaysPickLivePhoto={db.dto.auSel_AllLivePhoto}")

    if not db.dto.auSelEnable or not assets: return []

    active = any([
        db.dto.auSel_Earlier > 0, db.dto.auSel_Later > 0,
        db.dto.auSel_ExifRicher > 0, db.dto.auSel_ExifPoorer > 0,
        db.dto.auSel_BiggerSize > 0, db.dto.auSel_SmallerSize > 0,
        db.dto.auSel_BiggerDimensions > 0, db.dto.auSel_SmallerDimensions > 0,
        db.dto.auSel_NameLonger > 0, db.dto.auSel_NameShorter > 0,
    ])

    if not active: return []

    grpAssets = _groupAssetsByCondGroup(assets)
    lg.info(f"[autoSel] Grouped {len(assets)} assets into {len(grpAssets)} groups")

    selIds = []

    for grpId, grpAss in grpAssets.items():
        lg.info(f"[autoSel] Processing group {grpId} with {len(grpAss)} assets: {[a.autoId for a in grpAss]}")

        liveIds = _checkAlwaysPickLivePhoto(grpAss, grpId)
        if liveIds:
            selIds.extend(liveIds)
            lg.info(f"[autoSel] Group {grpId}: Selected ALL LivePhoto assets {liveIds}")
            continue

        if _shouldSkipGroupBy(grpAss, grpId):
            lg.info(f"[autoSel] Group {grpId}: Skipping group due to low similarity photos")
            continue

        bestId = _selectBestAsset(grpAss)
        if bestId:
            selIds.append(bestId)
            lg.info(f"[autoSel] Group {grpId}: Selected best weighted asset {bestId}")
        else:
            lg.warn(f"[autoSel] Group {grpId}: No best asset found despite having {len(grpAss)} assets")

    lg.info(f"[autoSel] Final selection: {len(selIds)} assets: {selIds}")
    return selIds


def _shouldSkipGroupBy(grpAssets: List[models.Asset], grpId: int) -> bool:
    lg.info(f"[autoSel] ------ Group[ {grpId} ] assets[ {len(grpAssets)} ]------")

    for ass in grpAssets:
        if hasattr(ass, 'view') and hasattr(ass.view, 'score'):
            scr = ass.view.score
            lg.info(f"[autoSel] Group {grpId}: Asset {ass.autoId} has view.score = {scr}")
        else:
            lg.warn(f"[autoSel] Group {grpId}: Asset {ass.autoId} missing view.score attribute")

    if not db.dto.auSel_SkipLowSim: return False

    hasLow = False
    lowAssets = []

    for ass in grpAssets:
        if hasattr(ass, 'view') and hasattr(ass.view, 'score'):
            scr = ass.view.score
            if scr != 0.0 and scr <= 0.96:
                hasLow = True
                lowAssets.append(f"{ass.autoId}(score={scr})")
                lg.info(f"[autoSel] Group {grpId}: Asset {ass.autoId} has LOW similarity (score={scr} <= 0.96)")
        else:
            hasLow = True
            lowAssets.append(f"{ass.autoId}(no score)")

    if hasLow:
        lg.info(f"[autoSel] Group {grpId}: SKIPPING group due to low similarity assets: {lowAssets}")
        return True

    lg.info(f"[autoSel] Group {grpId}: All assets have high similarity, processing group")
    return False


def _groupAssetsByCondGroup(assets: List[models.Asset]) -> dict:
    lg.info(f"[autoSel] Starting grouping for {len(assets)} assets")
    grpAssets = {}

    for ass in assets:
        grpId = ass.view.condGrpId if hasattr(ass, 'view') and hasattr(ass.view, 'condGrpId') else None
        if grpId is None:
            grpId = ass.autoId
            lg.debug(f"[autoSel] Asset {ass.autoId}: No condGrpId, using autoId as groupId")
        else:
            lg.debug(f"[autoSel] Asset {ass.autoId}: Using condGrpId {grpId}")

        if grpId not in grpAssets: grpAssets[grpId] = []
        grpAssets[grpId].append(ass)

    for grpId, grpAss in grpAssets.items():
        assIds = [a.autoId for a in grpAss]
        lg.info(f"[autoSel] Group {grpId}: Contains {len(grpAss)} assets: {assIds}")

    return grpAssets


def _selectBestAsset(grpAssets: List[models.Asset]) -> int:
    if not grpAssets: raise RuntimeError("No Group")

    def collectMetrics(assets: List[models.Asset]) -> List[AssetMetrics]:
        metrics = []
        for ass in assets:
            dt = None
            if ass.jsonExif:
                dt = ass.jsonExif.dateTimeOriginal or ass.fileCreatedAt

            exfCnt = _countExifFields(ass.jsonExif) if ass.jsonExif else 0
            fileSz = ass.jsonExif.fileSizeInByte if ass.jsonExif and ass.jsonExif.fileSizeInByte else 0

            dim = 0
            if ass.jsonExif:
                w = ass.jsonExif.exifImageWidth or 0
                h = ass.jsonExif.exifImageHeight or 0
                dim = w + h

            nameLen = len(ass.originalFileName) if ass.originalFileName else 0

            ndt = normalizeDate(dt)
            metrics.append(AssetMetrics( aid=ass.autoId, dt=ndt, exfCnt=exfCnt, fileSz=fileSz, dim=dim, nameLen=nameLen))
        return metrics

    def calcScore(idx: int, met: List[AssetMetrics]) -> Tuple[int, List[str]]:
        score = 0
        details = []

        def addScore(weight: int, vals: List, isMax: bool, label: str):
            nonlocal score, details
            if weight > 0 and len(set(vals)) > 1:
                target = max(vals) if isMax else min(vals)
                if vals[idx] == target:
                    pts = weight * 10
                    score += pts
                    details.append(f"{label}+{pts}")

        dates = [m.dt for m in met]
        validDates = [d for d in dates if d]

        if dates[idx] and validDates and len(set(validDates)) > 1:
            if db.dto.auSel_Earlier > 0 and dates[idx] == min(validDates):
                pts = db.dto.auSel_Earlier * 10
                score += pts
                details.append(f"Earlier+{pts}")
            if db.dto.auSel_Later > 0 and dates[idx] == max(validDates):
                pts = db.dto.auSel_Later * 10
                score += pts
                details.append(f"Later+{pts}")

        addScore(db.dto.auSel_ExifRicher, [m.exfCnt for m in met], True, "ExifRich")
        addScore(db.dto.auSel_ExifPoorer, [m.exfCnt for m in met], False, "ExifPoor")
        addScore(db.dto.auSel_BiggerSize, [m.fileSz for m in met], True, "BigSize")
        addScore(db.dto.auSel_SmallerSize, [m.fileSz for m in met], False, "SmallSize")
        addScore(db.dto.auSel_BiggerDimensions, [m.dim for m in met], True, "BigDim")
        addScore(db.dto.auSel_SmallerDimensions, [m.dim for m in met], False, "SmallDim")
        addScore(db.dto.auSel_NameLonger, [m.nameLen for m in met], True, "LongName")
        addScore(db.dto.auSel_NameShorter, [m.nameLen for m in met], False, "ShortName")

        return score, details

    met = collectMetrics(grpAssets)

    lg.info(f"[autoSel] Group comparison data:")
    for m in met:
        lg.info(f"[autoSel]   Asset {m.aid}: date={m.dt}, exifCount={m.exfCnt}, fileSize={m.fileSz}, dimensions={m.dim}, nameLen={m.nameLen}")

    bestAss = None
    bestScr = -1

    for i, ass in enumerate(grpAssets):
        scr, det = calcScore(i, met)
        lg.info(f"[autoSel] Asset {ass.autoId}: score={scr} ({', '.join(det) if det else 'no matches'})")

        if scr > bestScr:
            bestScr = scr
            bestAss = ass

    if not bestAss: raise RuntimeError("NotFound best Asset")
    return bestAss.autoId



def _checkAlwaysPickLivePhoto(grpAssets: List[models.Asset], grpId: int) -> List[int]:
    if not db.dto.auSel_AllLivePhoto: return []

    liveIds = []
    for ass in grpAssets:
        hasCID = ass.vdoId is not None
        hasPath = ass.pathVdo

        if hasCID or hasPath:
            liveIds.append(ass.autoId)
            lg.info(f"[autoSel] Group {grpId}: Found LivePhoto asset {ass.autoId} (CID={hasCID}, Path={bool(hasPath)})")

    if not liveIds: return []

    lg.info(f"[autoSel] Group {grpId}: Selecting ALL {len(liveIds)} LivePhoto assets: {liveIds}")
    return liveIds


def _countExifFields(exif) -> int:
    if not exif: return 0

    fields = [
        'dateTimeOriginal', 'modifyDate', 'make', 'model', 'lensModel',
        'fNumber', 'focalLength', 'exposureTime', 'iso',
        'latitude', 'longitude', 'city', 'state', 'country', 'description',
        'exifImageWidth', 'exifImageHeight', 'fileSizeInByte'
    ]

    return sum(1 for f in fields if hasattr(exif, f) and getattr(exif, f, None) is not None)
