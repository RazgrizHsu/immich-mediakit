import time
from typing import List, Tuple, Set, Callable, Optional

import db
from mod import models
from mod.models import IFnProg
from util import log

lg = log.get(__name__)


class SearchInfo:
    def __init__(self):
        self.asset: models.Asset
        self.bseVec: List[float] = []
        self.bseInfos: List[models.SimInfo] = []
        self.simAids: List[int] = []
        self.foundSimilar: bool = False
        self.hasVector: bool = False


class GroupSearchInfo:
    def __init__(self):
        self.allGroupAssets: List[models.Asset] = []
        self.groupCount: int = 0
        self.maxGroups: int = 1


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
    lg.info(f"[autoSel] Starting auto-selection, auSelEnable={db.dto.auSelEnable}, assets count={len(assets) if assets else 0}")
    lg.info(f"[autoSel] Weights: Earlier={db.dto.auSel_Earlier}, Later={db.dto.auSel_Later}, ExifRich={db.dto.auSel_ExifRicher}, ExifPoor={db.dto.auSel_ExifPoorer}, BigSize={db.dto.auSel_BiggerSize}, SmallSize={db.dto.auSel_SmallerSize}, BigDim={db.dto.auSel_BiggerDimensions}, SmallDim={db.dto.auSel_SmallerDimensions}, HighSim={db.dto.auSel_SkipLowSim}, AlwaysPickLivePhoto={db.dto.auSel_AllLivePhoto}")

    if not db.dto.auSelEnable or not assets:
        lg.info(f"[autoSel] Auto-selection disabled or no assets, returning empty")
        return []

    # Check if any weight is enabled
    hasActiveWeights = any([
        db.dto.auSel_Earlier > 0, db.dto.auSel_Later > 0,
        db.dto.auSel_ExifRicher > 0, db.dto.auSel_ExifPoorer > 0,
        db.dto.auSel_BiggerSize > 0, db.dto.auSel_SmallerSize > 0,
        db.dto.auSel_BiggerDimensions > 0, db.dto.auSel_SmallerDimensions > 0
    ])

    if not hasActiveWeights:
        lg.info(f"[autoSel] No active weights, returning empty")
        return []

    # Step 1: Group assets by similarity group first
    groupedAssets = _groupAssetsByCondGroup(assets)
    lg.info(f"[autoSel] Grouped {len(assets)} assets into {len(groupedAssets)} groups")

    selectedIds = []

    # Step 2: Process each group independently
    for groupId, groupAssets in groupedAssets.items():
        lg.info(f"[autoSel] Processing group {groupId} with {len(groupAssets)} assets: {[a.autoId for a in groupAssets]}")

        # Step 3: Check for LivePhoto preference
        livePhotoIds = _checkAlwaysPickLivePhoto(groupAssets, groupId)
        if livePhotoIds:
            selectedIds.extend(livePhotoIds)
            lg.info(f"[autoSel] Group {groupId}: Selected ALL LivePhoto assets {livePhotoIds}")
            continue

        # Step 4: Check if group should be skipped due to low similarity
        shouldSkip = _shouldSkipGroupBy(groupAssets, groupId)

        if shouldSkip:
            lg.info(f"[autoSel] Group {groupId}: Skipping group due to low similarity photos")
            continue

        # Step 5: Apply weight-based selection within the group
        bestAssetId = _selectBestAssetByWeights(groupAssets)
        if bestAssetId:
            selectedIds.append(bestAssetId)
            lg.info(f"[autoSel] Group {groupId}: Selected best weighted asset {bestAssetId}")
        else:
            lg.warn(f"[autoSel] Group {groupId}: No best asset found despite having {len(groupAssets)} assets")

    lg.info(f"[autoSel] Final selection: {len(selectedIds)} assets: {selectedIds}")
    return selectedIds


def _shouldSkipGroupBy(groupAssets: List[models.Asset], groupId: int) -> bool:
    lg.info(f"[autoSel] Group {groupId}: Checking similarity for {len(groupAssets)} assets")

    for asset in groupAssets:
        if hasattr(asset, 'view') and hasattr(asset.view, 'score'):
            score = asset.view.score
            lg.info(f"[autoSel] Group {groupId}: Asset {asset.autoId} has view.score = {score}")
        else:
            lg.warn(f"[autoSel] Group {groupId}: Asset {asset.autoId} missing view.score attribute")

    if not db.dto.auSel_SkipLowSim:
        lg.info(f"[autoSel] Group {groupId}: Similarity check disabled, processing group")
        return False

    hasLowSimilarity = False
    lowSimilarityAssets = []

    for asset in groupAssets:
        if hasattr(asset, 'view') and hasattr(asset.view, 'score'):
            score = asset.view.score

            if score != 0.0 and score <= 0.96:
                hasLowSimilarity = True
                lowSimilarityAssets.append(f"{asset.autoId}(score={score})")
                lg.info(f"[autoSel] Group {groupId}: Asset {asset.autoId} has LOW similarity (score={score} <= 0.96)")
            else:
                if score == 0.0:
                    lg.info(f"[autoSel] Group {groupId}: Asset {asset.autoId} is MAIN image (score={score})")
                else:
                    lg.info(f"[autoSel] Group {groupId}: Asset {asset.autoId} has HIGH similarity (score={score} > 0.96)")
        else:
            lg.warn(f"[autoSel] Group {groupId}: Asset {asset.autoId} missing view.score, treating as low similarity")
            hasLowSimilarity = True
            lowSimilarityAssets.append(f"{asset.autoId}(no score)")

    if hasLowSimilarity:
        lg.info(f"[autoSel] Group {groupId}: SKIPPING group due to low similarity assets: {lowSimilarityAssets}")
        return True
    else:
        lg.info(f"[autoSel] Group {groupId}: All assets have high similarity, processing group")
        return False


def _groupAssetsByCondGroup(assets: List[models.Asset]) -> dict:
    lg.info(f"[autoSel] Starting grouping for {len(assets)} assets")
    groupedAssets = {}

    for asset in assets:
        # Use condGrpId if available, otherwise group by autoId (each asset in its own group)
        groupId = getattr(asset.view, 'condGrpId', None) if hasattr(asset, 'view') and hasattr(asset.view, 'condGrpId') else None
        if groupId is None:
            groupId = asset.autoId  # Each asset becomes its own group
            lg.debug(f"[autoSel] Asset {asset.autoId}: No condGrpId, using autoId as groupId")
        else:
            lg.debug(f"[autoSel] Asset {asset.autoId}: Using condGrpId {groupId}")

        if groupId not in groupedAssets:
            groupedAssets[groupId] = []
        groupedAssets[groupId].append(asset)

    # Log the final grouping results
    for groupId, groupAssets in groupedAssets.items():
        assetIds = [a.autoId for a in groupAssets]
        lg.info(f"[autoSel] Group {groupId}: Contains {len(groupAssets)} assets: {assetIds}")

    return groupedAssets


def _selectBestAssetByWeights(groupAssets: List[models.Asset]) -> int:
    if not groupAssets: raise RuntimeError("No Group")

    bestAsset:models.Optional[models.Asset] = None
    bestScore = -1

    # Prepare comparison data for the group
    groupDates = []
    groupExifCounts = []
    groupFileSizes = []
    groupDimensions = []

    def normalizeDateForComparison(dt):
        if dt is None: return None
        try:
            if hasattr(dt, 'replace'):
                return dt.replace(microsecond=0)
            else:
                dtStr = str(dt)
                if '.' in dtStr and ('+' in dtStr or 'Z' in dtStr):
                    beforeDot = dtStr.split('.')[0]
                    afterDot = dtStr.split('.')[1]
                    if '+' in afterDot:
                        timezone = '+' + afterDot.split('+')[1]
                        return beforeDot + timezone
                    elif 'Z' in afterDot:
                        return beforeDot + 'Z'
                return dtStr
        except: return dt

    for asset in groupAssets:
        # Date
        dateTime = None
        if asset.jsonExif:
            dateTime = getattr(asset.jsonExif, 'dateTimeOriginal', None) or getattr(asset.jsonExif, 'fileCreatedAt', None)
        groupDates.append(normalizeDateForComparison(dateTime))

        # EXIF count
        exifCount = _countExifFields(asset.jsonExif) if asset.jsonExif else 0
        groupExifCounts.append(exifCount)

        # File size
        fileSize = getattr(asset.jsonExif, 'fileSizeInByte', 0) if asset.jsonExif else 0
        groupFileSizes.append(fileSize)

        # Dimensions (width + height)
        dimensions = 0
        if asset.jsonExif:
            width = getattr(asset.jsonExif, 'exifImageWidth', 0) or 0
            height = getattr(asset.jsonExif, 'exifImageHeight', 0) or 0
            dimensions = width + height
        groupDimensions.append(dimensions)

    # Debug: Log the comparison data
    lg.info(f"[autoSel] Group comparison data:")
    for i, asset in enumerate(groupAssets):
        lg.info(f"[autoSel]   Asset {asset.autoId}: date={groupDates[i]}, exifCount={groupExifCounts[i]}, fileSize={groupFileSizes[i]}, dimensions={groupDimensions[i]}")

    # Calculate score for each asset
    for i, asset in enumerate(groupAssets):
        score = 0
        scoreDetails = []

        # Earlier photos weight
        if db.dto.auSel_Earlier > 0 and groupDates[i]:
            validDates = [d for d in groupDates if d is not None]
            if validDates and len(set(validDates)) > 1 and groupDates[i] == min(validDates):
                score += db.dto.auSel_Earlier * 10
                scoreDetails.append(f"Earlier+{db.dto.auSel_Earlier * 10}")

        # Later photos weight
        if db.dto.auSel_Later > 0 and groupDates[i]:
            validDates = [d for d in groupDates if d is not None]
            if validDates and len(set(validDates)) > 1 and groupDates[i] == max(validDates):
                score += db.dto.auSel_Later * 10
                scoreDetails.append(f"Later+{db.dto.auSel_Later * 10}")

        # Richer EXIF weight
        if db.dto.auSel_ExifRicher > 0:
            if len(set(groupExifCounts)) > 1 and groupExifCounts[i] == max(groupExifCounts):
                score += db.dto.auSel_ExifRicher * 10
                scoreDetails.append(f"ExifRich+{db.dto.auSel_ExifRicher * 10}")

        # Poorer EXIF weight
        if db.dto.auSel_ExifPoorer > 0:
            if len(set(groupExifCounts)) > 1 and groupExifCounts[i] == min(groupExifCounts):
                score += db.dto.auSel_ExifPoorer * 10
                scoreDetails.append(f"ExifPoor+{db.dto.auSel_ExifPoorer * 10}")

        # Bigger file size weight
        if db.dto.auSel_BiggerSize > 0:
            if len(set(groupFileSizes)) > 1 and groupFileSizes[i] == max(groupFileSizes):
                score += db.dto.auSel_BiggerSize * 10
                scoreDetails.append(f"BigSize+{db.dto.auSel_BiggerSize * 10}")

        # Smaller file size weight
        if db.dto.auSel_SmallerSize > 0:
            if len(set(groupFileSizes)) > 1 and groupFileSizes[i] == min(groupFileSizes):
                score += db.dto.auSel_SmallerSize * 10
                scoreDetails.append(f"SmallSize+{db.dto.auSel_SmallerSize * 10}")

        # Bigger dimensions weight
        if db.dto.auSel_BiggerDimensions > 0:
            if len(set(groupDimensions)) > 1 and groupDimensions[i] == max(groupDimensions):
                score += db.dto.auSel_BiggerDimensions * 10
                scoreDetails.append(f"BigDim+{db.dto.auSel_BiggerDimensions * 10}")

        # Smaller dimensions weight
        if db.dto.auSel_SmallerDimensions > 0:
            if len(set(groupDimensions)) > 1 and groupDimensions[i] == min(groupDimensions):
                score += db.dto.auSel_SmallerDimensions * 10
                scoreDetails.append(f"SmallDim+{db.dto.auSel_SmallerDimensions * 10}")

        lg.info(f"[autoSel] Asset {asset.autoId}: score={score} ({', '.join(scoreDetails) if scoreDetails else 'no matches'})")

        if score > bestScore:
            bestScore = score
            bestAsset = asset

    if not bestAsset: raise RuntimeError("NotFound best Asset")

    return bestAsset.autoId



def _checkAlwaysPickLivePhoto(groupAssets: List[models.Asset], groupId: int) -> List[int]:
    if not db.dto.auSel_AllLivePhoto:
        lg.info(f"[autoSel] Group {groupId}: AlwaysPickLivePhoto disabled")
        return []

    livePhotoIds = []
    for asset in groupAssets:
        # hasCID = asset.jsonExif and hasattr(asset.jsonExif, 'livePhotoCID') and asset.jsonExif.livePhotoCID
        hasCID = asset.livePhotoVideoId is not None
        hasPath = asset.pathVdo

        if hasCID or hasPath:
            livePhotoIds.append(asset.autoId)
            lg.info(f"[autoSel] Group {groupId}: Found LivePhoto asset {asset.autoId} (CID={hasCID}, Path={bool(hasPath)})")

    if not livePhotoIds:
        lg.info(f"[autoSel] Group {groupId}: No LivePhoto assets found")
        return []

    lg.info(f"[autoSel] Group {groupId}: Selecting ALL {len(livePhotoIds)} LivePhoto assets: {livePhotoIds}")
    return livePhotoIds


def _countExifFields(exif) -> int:
    if not exif: return 0

    importantFields = [
        'dateTimeOriginal', 'modifyDate', 'make', 'model', 'lensModel',
        'fNumber', 'focalLength', 'exposureTime', 'iso',
        'latitude', 'longitude', 'city', 'state', 'country', 'description',
        'exifImageWidth', 'exifImageHeight', 'fileSizeInByte'
    ]

    count = 0
    for field in importantFields:
        if hasattr(exif, field) and getattr(exif, field) is not None:
            count += 1

    return count
