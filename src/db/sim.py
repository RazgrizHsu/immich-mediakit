import time
from typing import List, Tuple, Set, Callable

import db
from mod import models
from mod.models import IFnProg
from util import log

lg = log.get(__name__)


class SearchResult:

    def __init__(self):
        self.asset: models.Asset
        self.bseVec: List[float] = []
        self.bseInfos: List[models.SimInfo] = []
        self.simAids: List[int] = []
        self.foundSimilar: bool = False
        self.hasVector: bool = False


class GroupSearchResult:
    def __init__(self):
        self.allGroupAssets: List[models.Asset] = []
        self.groupCount: int = 0
        self.maxGroups: int = 1


def createProgressReporter(doReport: IFnProg) -> Callable[[str], Tuple[int, int]]:
    def autoReport(msg: str) -> Tuple[int, int]:
        cntAll = db.pics.count()
        cntOk = db.pics.countSimOk(1)
        progress = round(cntOk / cntAll * 100, 2) if cntAll > 0 else 0
        doReport(progress, msg)
        return cntOk, cntAll
    return autoReport


def checkGroupConditions(assets: List[models.Asset]) -> bool:
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
            baseDate = str(getattr(baseExif, 'fileCreatedAt', ''))[:10] if hasattr(baseExif, 'fileCreatedAt') else ''
            assetDate = str(getattr(exif, 'fileCreatedAt', ''))[:10] if hasattr(exif, 'fileCreatedAt') else ''
            if baseDate != assetDate: return False

        if doWidth:
            baseWidth = getattr(baseExif, 'exifImageWidth', None)
            assetWidth = getattr(exif, 'exifImageWidth', None)
            if baseWidth != assetWidth: return False

        if doHeight:
            baseHeight = getattr(baseExif, 'exifImageHeight', None)
            assetHeight = getattr(exif, 'exifImageHeight', None)
            if baseHeight != assetHeight: return False

        if doSize:
            baseSize = getattr(baseExif, 'fileSizeInByte', None)
            assetSize = getattr(exif, 'fileSizeInByte', None)
            if baseSize != assetSize: return False

    return True


def findAssetCandidate(autoId: int, taskArgs: dict) -> models.Asset:
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


def searchSimilar(
    asset: models.Asset, thMin: float, thMax: float,
    autoReport: Callable[[str], Tuple[int, int]],
    isFromUrl: bool, doReport: IFnProg
) -> SearchResult:
    result = SearchResult()
    result.asset = asset
    cntFnd = 0

    while True:
        if cntFnd <= 0:
            msg = f"[sim:fnd] search #{asset.autoId}, thresholds[{thMin:.2f}-{thMax:.2f}]"
            doReport(10, msg)

        time.sleep(0.1)
        cntFnd += 1

        # Search for similar assets
        bseVec, bseInfos = db.vecs.findSimiliar(asset.autoId, thMin, thMax)
        result.bseVec = bseVec
        result.bseInfos = bseInfos

        # Check if vector exists
        if not bseInfos:
            lg.warn(f"[sim:fnd] asset #{asset.autoId} not found any similar, may not store vector")
            db.pics.setVectoredBy(asset, 0)
            result.hasVector = False

            if isFromUrl:
                msg = f"[sim:fnd] Asset #{asset.autoId} has no vector stored"
                doReport(100, msg)
                return result

            # Try find next asset
            nextAss = db.pics.getAnyNonSim()
            if not nextAss:
                msg = f"[sim:fnd] No more images to continue searching"
                doReport(100, msg)
                return result

            lg.info(f"[sim:fnd] No vector for #{asset.autoId}, next: #{nextAss.autoId}")
            autoReport(f"No vector for #{asset.autoId}, continuing to #{nextAss.autoId}...")

            asset = nextAss
            result.asset = asset
            continue

        result.hasVector = True
        simAids = [i.aid for i in bseInfos if not i.isSelf]
        result.simAids = simAids

        # Check if only contains self
        if not simAids:
            lg.info(f"[sim:fnd] NoFound #{asset.autoId}")
            db.pics.setSimInfos(asset.autoId, bseInfos, isOk=1)
            result.foundSimilar = False

            if isFromUrl:
                msg = f"[sim:fnd] Asset #{asset.autoId} no similar found"
                doReport(100, msg)
                return result

            # Try find next asset
            nextAss = db.pics.getAnyNonSim()
            if not nextAss:
                msg = f"[sim:fnd] No more images to continue searching"
                doReport(100, msg)
                return result

            lg.info(f"[sim:fnd] Next: #{nextAss.autoId}")
            autoReport(f"No similar found for #{asset.autoId}, continuing to #{nextAss.autoId}...")
            asset = nextAss
            result.asset = asset
            continue

        # Found similar assets, check group conditions if enabled
        if db.dto.simCondGrpMode:
            similarAssets = [asset] + [db.pics.getByAutoId(aid) for aid in simAids if db.pics.getByAutoId(aid)]

            if not checkGroupConditions(similarAssets):
                lg.info(f"[sim:fnd] Group conditions not met for #{asset.autoId}, marking as resolved and continuing")
                db.pics.setSimInfos(asset.autoId, bseInfos, isOk=1)

                if not isFromUrl:
                    nextAss = db.pics.getAnyNonSim()
                    if not nextAss:
                        msg = f"[sim:fnd] No more images to continue searching"
                        doReport(100, msg)
                        return result

                    lg.info(f"[sim:fnd] Continuing to next: #{nextAss.autoId}")
                    autoReport(f"Group conditions not met for #{asset.autoId}, continuing to #{nextAss.autoId}...")
                    asset = nextAss
                    result.asset = asset
                    continue
                else:
                    msg = f"[sim:fnd] Asset #{asset.autoId} group conditions not met"
                    doReport(100, msg)
                    return result

        # Group conditions met or not in group mode, found similar assets
        result.foundSimilar = True
        break

    return result


def processChildren(asset: models.Asset, bseInfos: List[models.SimInfo], simAids: List[int],
                         thMin: float, thMax: float, maxDepth: int, maxItems: int, doReport: IFnProg) -> Set[int]:
    rootGID = asset.autoId
    db.pics.setSimGIDs(asset.autoId, rootGID)
    db.pics.setSimInfos(asset.autoId, bseInfos)

    doneIds = {asset.autoId}
    simQ = [(aid, 0) for aid in simAids]

    while simQ:
        aid, depth = simQ.pop(0)
        if aid in doneIds:
            continue

        doneIds.add(aid)
        doReport(50, f"Processing children similar photo #{aid} depth({depth}) count({len(doneIds)})")

        try:
            ass = db.pics.getByAutoId(aid)
            if ass.simOk:
                continue  # ignore already resolved

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


def searchCondGroups( currentAssets: List[models.Asset], maxGroups: int, thMin: float, thMax: float, maxDepth: int, maxItems: int, doReport: IFnProg) -> GroupSearchResult:
    result = GroupSearchResult()
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
            if not checkGroupConditions(nextSimilarAssets):
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
