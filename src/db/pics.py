import json
import sqlite3
from sqlite3 import Cursor
from typing import Optional, List, Callable
from contextlib import contextmanager

from conf import envs
from util import log
from mod import models
from mod.bse.baseModel import BaseDictModel
from util.err import mkErr, tracebk

lg = log.get(__name__)

pathDb = envs.mkitData + 'pics.db'

@contextmanager
def mkConn():
    """Context manager for database connections"""
    conn = None
    try:

        conn = sqlite3.connect(pathDb, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        yield conn
    finally:
        if conn:
            conn.close()

def close():
    # Deprecated - connections are now managed by context manager
    return True


def init():
    try:
        with mkConn() as conn:
            c = conn.cursor()

            c.execute('''
                Create Table If Not Exists assets (
                    autoId           INTEGER Primary Key AUTOINCREMENT,
                    id               TEXT Unique,
                    ownerId          TEXT,
                    deviceId         TEXT,
                    type             TEXT,
                    originalFileName TEXT,
                    fileCreatedAt    TEXT,
                    fileModifiedAt   TEXT,
                    isFavorite       INTEGER,
                    isVisible        INTEGER,
                    isArchived       INTEGER,
                    libraryId        TEXT,
                    localDateTime    TEXT,
                    thumbnail_path   TEXT,
                    preview_path     TEXT,
                    fullsize_path    TEXT,
                    jsonExif         TEXT Default '{}',
                    size             INTEGER Default 0,
                    isVectored       INTEGER Default 0,
                    simOk            INTEGER Default 0,
                    simInfos         TEXT Default '[]',
                    simGID           INTEGER Default 0
                )
                ''')

            c.execute('''
                Create Table If Not Exists users (
                    id     TEXT Primary Key,
                    name   TEXT,
                    email  TEXT,
                    apiKey TEXT
                )
                ''')

            conn.commit()

            lg.info( f"[pics] db connected: {pathDb}" )

        return True
    except Exception as e:
        raise mkErr("Failed to initialize duplicate photo database", e)

def clearAll():
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Drop Table If Exists assets")
            c.execute("Drop Table If Exists users")
            conn.commit()
        return init()
    except Exception as e:
        raise mkErr("Failed to clear database", e)


def clearBy(usrId):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = "Delete From assets WHERE ownerId = ?"
            c.execute(sql, (usrId,))
            cnt = c.rowcount
            conn.commit()

            lg.info( f"[pics] delete userId[ {usrId} ] assets[ {cnt} ]" )
            return cnt
    except Exception as e:
        raise mkErr(f"Failed to del assets by userId[{usrId}]", e)


def count(usrId=None):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = "Select Count(*) From assets"
            if usrId:
                sql += " Where ownerId = ?"
                c.execute(sql, (usrId,))
            else:
                c.execute(sql)
            cnt = c.fetchone()[0]
            return cnt
    except Exception as e:
        raise mkErr("Failed to get asset count", e)


#========================================================================
# quary
#========================================================================
def getByAutoId(autoId) -> Optional[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Select * From assets Where autoId= ?", (autoId,))
            row = c.fetchone()
            if row is None: return None
            asset = models.Asset.fromDB(c, row)
            return asset
    except Exception as e:
        raise mkErr("Failed to get asset information", e)

def getById(assId) -> Optional[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Select * From assets Where id = ?", (assId,))
            row = c.fetchone()
            if row is None: return None
            asset = models.Asset.fromDB(c, row)
            return asset
    except Exception as e:
        raise mkErr("Failed to get asset information", e)

def getAllByUsrId(usrId: str) -> List[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute(f"Select * From assets Where ownerId = ? ", (usrId,))
            rows = c.fetchall()
            if not rows: return []
            assets = [models.Asset.fromDB(c, row) for row in rows]
            return assets
    except Exception as e:
        raise mkErr(f"Failed to get asset by userId[{usrId}]", e)

def getAllByIds(ids: List[str]) -> List[models.Asset]:
    try:
        if not ids: return []
        with mkConn() as conn:
            c = conn.cursor()
            qargs = ','.join(['?' for _ in ids])
            c.execute(f"Select * From assets Where id IN ({qargs})", ids)
            rows = c.fetchall()
            if not rows: return []
            assets = [models.Asset.fromDB(c, row) for row in rows]
            return assets
    except Exception as e:
        raise mkErr(f"Failed to get asset by ids[{ids}]", e)


def getAll(count=0) -> list[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            if not count:
                sql = "Select * From assets"
                c.execute(sql)
            else:
                sql = "Select * From assets LIMIT ?"
                c.execute(sql, (count,))
            rows = c.fetchall()
            if not rows: return []
            assets = [models.Asset.fromDB(c, row) for row in rows]
            return assets
    except Exception as e:
        raise mkErr("Failed to get all asset information", e)


def getAllNonVector() -> list[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = "Select * From assets WHERE isVectored=0"
            c.execute(sql)
            rows = c.fetchall()
            if not rows: return []
            assets = [models.Asset.fromDB(c, row) for row in rows]
            return assets
    except Exception as e:
        raise mkErr("Failed to get all asset information", e)

#------------------------------------------------------------------------
# paged
#------------------------------------------------------------------------
def countFiltered(usrId="", opts="all", search="", favOnly=False):
    try:
        cds = []
        pms = []

        if usrId:
            cds.append("ownerId = ?")
            pms.append(usrId)

        if favOnly:
            cds.append("isFavorite = 1")

        if opts == "with_vectors":
            cds.append("isVectored = 1")
        elif opts == "without_vectors":
            cds.append("isVectored = 0")

        if search and len(search.strip()) > 0:
            cds.append("originalFileName LIKE ?")
            pms.append(f"%{search}%")

        query = "Select Count(*) From assets"
        if cds: query += " WHERE " + " AND ".join(cds)


        with mkConn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, pms)
            return cursor.fetchone()[0]
    except Exception as e:
        lg.error(f"Error counting assets: {str(e)}")
        return 0


def getFiltered(
    usrId="",
    opts="all", search="", onlyFav=False,
    page=1, pageSize=24
) -> list[models.Asset]:
    try:
        cds = []
        pms = []

        if usrId:
            cds.append("ownerId = ?")
            pms.append(usrId)

        if onlyFav:
            cds.append("isFavorite = 1")

        if opts == "with_vectors":
            cds.append("isVectored = 1")
        elif opts == "without_vectors":
            cds.append("isVectored = 0")

        if search and len(search.strip()) > 0:
            cds.append("originalFileName LIKE ?")
            pms.append(f"%{search}%")

        query = "Select * From assets"
        if cds:
            query += " WHERE " + " AND ".join(cds)

        query += f" Order By autoId DESC"
        # query += f" ORDER BY {sort} {'DESC' if sortOrd == 'desc' else 'ASC'}"
        query += f" LIMIT {pageSize} OFFSET {(page - 1) * pageSize}"

        with mkConn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, pms)
            assets = []
            for row in cursor.fetchall():
                asset = models.Asset.fromDB(cursor, row)
                assets.append(asset)
            return assets
    except Exception as e:
        lg.error(f"Error fetching assets: {str(e)}")
        return []




#========================================================================
# update
#========================================================================

def updVecBy(asset: models.Asset, done=1, cur: Cursor = None):
    try:
        if cur:
            # Use provided cursor (for transactions)
            cur.execute("UPDATE assets SET isVectored=? WHERE id = ?", (done, asset.id))
        else:
            # Use context manager for standalone operation
            with mkConn() as conn:
                c = conn.cursor()
                c.execute("UPDATE assets SET isVectored=? WHERE id = ?", (done, asset.id))
                conn.commit()
    except Exception as e:
        raise mkErr(f"Failed to updateVecBy: {asset}", e)

def saveBy(asset: dict, c: Cursor):  #, onExist:Callable[[models.Asset],None]):
    try:
        assId = asset.get('id', None )
        if not assId: return False

        if not isinstance( assId, str ): assId = str(assId)

        exifInfo = asset.get('exifInfo', {})
        jsonExif = None
        if exifInfo:
            try:
                jsonExif = json.dumps(exifInfo, ensure_ascii=False, default=BaseDictModel.jsonSerializer)
                # lg.info(f"json: {jsonExif}")
            except Exception as e:
                raise mkErr("[pics.save] Error converting EXIF to JSON", e)

        c.execute("Select autoId, id From assets Where id = ?", (assId,))
        row = c.fetchone()

        if row is None:
            c.execute('''
                Insert Into assets (id, ownerId, deviceId, type, originalFileName,
                fileCreatedAt, fileModifiedAt, isFavorite, isVisible, isArchived,
                libraryId, localDateTime, thumbnail_path, preview_path, fullsize_path, jsonExif)
                Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assId,
                str(asset.get('ownerId')),
                asset.get('deviceId'),
                asset.get('type'),
                asset.get('originalFileName'),
                asset.get('fileCreatedAt'),
                asset.get('fileModifiedAt'),
                1 if asset.get('isFavorite') else 0,
                1 if asset.get('isVisible') else 0,
                1 if asset.get('isArchived') else 0,
                asset.get('libraryId'),
                asset.get('localDateTime'),
                asset.get('thumbnail_path'),
                asset.get('preview_path'),
                asset.get('fullsize_path', asset.get('originalPath')),
                jsonExif,
            ))

            return True

        # else:
        #     lg.info(f"asset already exists, update it..")
        #     ass = models.Asset.fromDB(c, row)
        #     if onExist: onExist( ass )
        #
        #     c.execute('''
        #         UPDATE assets SET
        #         simOk = 0, simGID = 0, simInfos = '[]',
        #         ownerId = ?, deviceId = ?, type = ?, originalFileName = ?,
        #         fileCreatedAt = ?, fileModifiedAt = ?, isFavorite = ?, isVisible = ?, isArchived = ?,
        #         libraryId = ?, localDateTime = ?, thumbnail_path = ?, preview_path = ?, fullsize_path = ?, jsonExif = ?
        #         WHERE id = ?
        #     ''', (
        #         asset.get('ownerId'),
        #         asset.get('deviceId'),
        #         asset.get('type'),
        #         asset.get('originalFileName'),
        #         asset.get('fileCreatedAt'),
        #         asset.get('fileModifiedAt'),
        #         1 if asset.get('isFavorite') else 0,
        #         1 if asset.get('isVisible') else 0,
        #         1 if asset.get('isArchived') else 0,
        #         asset.get('libraryId'),
        #         asset.get('localDateTime'),
        #         asset.get('thumbnail_path'),
        #         asset.get('preview_path'),
        #         asset.get('fullsize_path', asset.get('originalPath')),
        #         jsonExif,
        #         asset.get('id')
        #     ))
        return False # ignore duplicates
    except Exception as e:
        raise mkErr("Failed to save asset information", e)


# def deleteForUsr(usrId):
#     import db.vecs as vecs
#     try:
#         with mkConn() as conn:
#             c = conn.cursor()
#             c.execute("Select id From assets Where ownerId = ?", (usrId,))
#             assIds = [row[0] for row in c.fetchall()]
#             lg.info(f"[pics] delete pics[{len(assIds)}] for usrId[{usrId}]")
#             c.execute("Delete From assets Where ownerId = ?", (usrId,))
#             conn.commit()
#             lg.info(f"[pics] delete vectors for usrId[{usrId}]")
#             for assId in assIds: vecs.deleteBy(assId)
#             return True
#     except Exception as e:
#         raise mkErr("Failed to delete user assets", e)


#========================================================================
# sim
#========================================================================

def getAnyNonSim() -> Optional[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Select * From assets Where simOk!=1 AND json_array_length(simINfos) == 0")
            row = c.fetchone()
            if row is None: return None
            asset = models.Asset.fromDB(c, row)
            return asset
    except Exception as e:
        raise mkErr("Failed to get asset information", e)

def countSimOk(isOk=0):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM assets WHERE isVectored = 1 AND simOk = ?", (isOk,))
            count = c.fetchone()[0]
            # lg.info(f"[pics] count isOk[{isOk}] cnt[{count}]")
            return count
    except Exception as e:
        raise mkErr(f"Failed to count assets with simOk[{isOk}]", e)


def getAssetsByGID(gid: int) -> list[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM assets 
                WHERE simGID = ? AND json_array_length(simInfos) > 1
                ORDER BY json_array_length(simInfos) DESC, autoId
            """, (gid,))
            assets = []
            for row in c.fetchall():
                asset = models.Asset.fromDB(c, row)
                assets.append(asset)
            return assets
    except Exception as e:
        lg.error(f"Error fetching assets by GID: {str(e)}")
        return []


def getSimGroup(assId: str) -> Optional[List[models.Asset]]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM assets WHERE id = ?", (assId,))
            row = c.fetchone()
            if row is None:
                lg.warn(f"[pics] SimGroup Root asset {assId} not found")
                return None

            rootAsset = models.Asset.fromDB(c, row)
            rst = [rootAsset]

            if not rootAsset.simInfos or len(rootAsset.simInfos) <= 1: return rst

            simIds = [info.id for info in rootAsset.simInfos]
            if not simIds: return [rootAsset]

            qargs = ','.join(['?' for _ in simIds])
            c.execute(f"SELECT * FROM assets WHERE id IN ({qargs})", simIds)

            rows = c.fetchall()

            assets = [models.Asset.fromDB(c, row) for row in rows]

            assetMap = {asset.id: asset for asset in assets}

            # rootAsset.simInfos score, desc
            sortAss = []
            for simInfo in sorted(rootAsset.simInfos, key=lambda x: x.score or 0, reverse=True):
                if simInfo.id in assetMap:
                    sortAss.append(assetMap[simInfo.id])

            rst.extend(sortAss)

            return sortAss
    except Exception as e:
        raise mkErr(f"Failed to get similar group for root {assId}", e)


def setSimIds(assId: str, infos: List[models.SimInfo], isOk: int = 0):
    if not infos or len(infos) <= 0:
        lg.warn(f"Can't setSimIds id[{assId}] by [{type(infos)}], {tracebk.format_exc()}")
        return

    try:
        with mkConn() as conn:
            c = conn.cursor()

            conn.execute("BEGIN TRANSACTION")

            try:
                c.execute("SELECT id, simGID FROM assets WHERE id = ?", (assId,))
                curRow = c.fetchone()
                if not curRow: raise RuntimeError(f"Asset {assId} not found")

                curGID = curRow[1]

                simDicts = [sim.toDict() for sim in infos] if infos else []
                c.execute("UPDATE assets SET simInfos = ?, simOk = ? WHERE id = ?", (json.dumps(simDicts), isOk, assId))

                highSimIds = [sim.id for sim in infos if sim.score and sim.score > 0.9 and sim.id != assId]
                if not highSimIds:
                    conn.commit()
                    lg.info(f"[sim] Updated simInfo[{len(infos)}] simOk[{isOk}] to assId[{assId}]")
                    return True

                highSimIds.append(assId)

                qargs = ','.join(['?' for _ in highSimIds])
                c.execute(f"SELECT id, simGID, simInfos FROM assets WHERE id IN ({qargs})", highSimIds)

                grpAssets = {}
                existGIDs = set()
                for row in c.fetchall():
                    aId, gid, simJson = row
                    grpAssets[aId] = {
                        'gid': gid,
                        'simInfos': json.loads(simJson) if simJson else []
                    }
                    if gid: existGIDs.add(gid)

                if len(existGIDs) > 1:
                    minGID = min(existGIDs)
                    otherGIDs = existGIDs - {minGID}
                    qargs = ','.join(['?' for _ in otherGIDs])
                    c.execute(f"UPDATE assets SET simGID = ? WHERE simGID IN ({qargs})", [minGID] + list(otherGIDs))

                    for aId in grpAssets:
                        if grpAssets[aId]['gid'] in otherGIDs:
                            grpAssets[aId]['gid'] = minGID

                connCounts = {}
                for aId in highSimIds:
                    cnt = 0
                    if aId in grpAssets:
                        for sim in grpAssets[aId]['simInfos']:
                            if sim.get('score', 0) > 0.9 and sim.get('id') in highSimIds:
                                cnt += 1
                    connCounts[aId] = cnt

                repId = max(highSimIds, key=lambda x: (connCounts.get(x, 0), x))

                newGID = None
                if existGIDs:
                    newGID = min(existGIDs) if existGIDs else None
                else:
                    c.execute("SELECT MAX(simGID) FROM assets")
                    maxGID = c.fetchone()[0]
                    newGID = (maxGID or 0) + 1

                qargs = ','.join(['?' for _ in highSimIds])
                c.execute(f"UPDATE assets SET simGID = ? WHERE id IN ({qargs})", [newGID] + highSimIds)

                conn.commit()
                lg.info(f"[pics] Updated simInfo[{len(infos)}] simOk[{isOk}] to assId[{assId}], group[{newGID}] with {len(highSimIds)} members")
                return True
            except Exception as e:
                conn.rollback()
                raise e
    except Exception as e:
        raise mkErr("Failed to set similar IDs", e)


def deleteBy(assets: List[models.Asset]):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            autoIds = [ass.autoId for ass in assets]
            assIds = [ass.id for ass in assets]
            if not autoIds: return 0

            qargs = ','.join(['?' for _ in autoIds])
            c.execute(f"DELETE FROM assets WHERE autoId IN ({qargs})", autoIds)
            conn.commit()
            count = c.rowcount
            lg.info(f"[pics] delete by autoIds[{len(autoIds)}] rst[{count}]")
            
            # Delete vectors from Qdrant
            if assIds:
                import db.vecs as vecs
                try:
                    vecs.deleteBy(assIds)
                    lg.info(f"[pics] deleted vectors for {len(assIds)} assets")
                except Exception as e:
                    lg.error(f"[pics] Failed to delete vectors: {str(e)}")
            
            return count
    except Exception as e:
        raise mkErr("Failed to clear similarity results:", e)

def setResloveBy(assets: List[models.Asset]):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            autoIds = [ass.autoId for ass in assets]
            if not autoIds: return 0

            qargs = ','.join(['?' for _ in autoIds])
            c.execute(f"UPDATE assets SET simOk = 1, simGID = 0, simInfos = '[]' WHERE autoId IN ({qargs})", autoIds)
            conn.commit()
            count = c.rowcount
            lg.info(f"[pics] set simOk by autoIds[{len(autoIds)}] rst[{count}]")
            return count
    except Exception as e:
        raise mkErr("Failed to clear similarity results:", e)

def clearAllSimIds():
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("UPDATE assets SET simOk = 0, simInfos = '[]'")
            conn.commit()
            count = c.rowcount
            lg.info(f"Cleared similarity results for {count} assets")
            return count
    except Exception as e:
        raise mkErr("Failed to clear similarity results:", e)


def countHasSimIds(isOk=0):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = '''
                SELECT COUNT(*) FROM assets 
                WHERE simOk = ? AND json_array_length(simInfos) > 0
            '''
            c.execute(sql, (isOk,))
            row = c.fetchone()
            count = row[0] if row else 0
            lg.info(f"[pics] count have simInfos and type[{isOk}] cnt[{count}]")
            return count
    except Exception as e:
        raise mkErr(f"Failed to count assets have simInfos with simOk[{isOk}]", e)


# simOk mean that already resolve by user
def getAnySimPending() -> Optional[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM assets 
                WHERE
                    simOk = 0 AND json_array_length(simInfos) > 1
                LIMIT 1
            """)
            row = c.fetchone()
            return models.Asset.fromDB(c, row) if row else None
    except Exception as e:
        raise mkErr("Failed to get pending assets", e)

def getAllSimOks(isOk=0) -> List[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM assets 
                WHERE
                    simOk = ? AND json_array_length(simInfos) > 1
                ORDER BY autoId
            """, (isOk,))
            rows = c.fetchall()
            if not rows: return []
            assets = [models.Asset.fromDB(c, row) for row in rows]
            return assets
    except Exception as e:
        raise mkErr("Failed to get all simOk assets", e)


# auto mark simOk=1 if simInfos only includes self
def setSimAutoMark():
    try:
        with mkConn() as cnn:
            c = cnn.cursor()
            c.execute("""
                UPDATE assets 
                SET simOk = 1
                WHERE
                    simOk = 0 AND json_array_length(simInfos) = 1
                    AND EXISTS 
                    (
                        SELECT 1 FROM json_each(simInfos) si
                            WHERE json_extract(si.value, '$.isSelf') = 1
                    )
            """)
            cnn.commit()
    except Exception as e:
        raise mkErr(f"Failed to count assets pending", e)

# select have simInfos and simInfos not only isSelf
def countSimPending():
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = '''
                WITH grpReps AS (
                    SELECT simGID, MIN(autoId) as repAutoId
                    FROM assets
                    WHERE simOk = 0 AND json_array_length(simInfos) > 1 AND simGID IS NOT NULL
                    GROUP BY simGID
                )
                SELECT COUNT(*) FROM (
                    SELECT a.autoId FROM assets a
                    LEFT JOIN grpReps g ON a.simGID = g.simGID
                    WHERE a.simOk = 0 AND json_array_length(a.simInfos) > 1
                    AND (
                        (a.simGID IS NULL) OR 
                        (a.simGID IS NOT NULL AND a.autoId = g.repAutoId)
                    )
                )
            '''
            c.execute(sql)
            cnt = c.fetchone()[0]
            return cnt
    except Exception as e:
        raise mkErr(f"Failed to count assets pending", e)


def getPendingPaged(page=1, size=20) -> list[models.Asset]:
    try:
        sql = '''
            WITH grpReps AS (
                SELECT simGID, MIN(autoId) as repAutoId
                FROM assets
                WHERE simOk = 0 AND json_array_length(simInfos) > 1 AND simGID IS NOT NULL
                GROUP BY simGID
            )
            SELECT a.* FROM assets a
            LEFT JOIN grpReps g ON a.simGID = g.simGID
            WHERE a.simOk = 0 AND json_array_length(a.simInfos) > 1
            AND (
                (a.simGID IS NULL) OR 
                (a.simGID IS NOT NULL AND a.autoId = g.repAutoId)
            )
            ORDER BY json_array_length(a.simInfos) DESC, a.autoId
            LIMIT ? OFFSET ?
        '''

        with mkConn() as conn:
            cursor = conn.cursor()
            offset = (page - 1) * size
            cursor.execute(sql, (size, offset))

            leaders = []
            for row in cursor.fetchall():
                asset = models.Asset.fromDB(cursor, row)
                leaders.append(asset)

            if not leaders: return []

            allRelIds = set()
            for leader in leaders:
                for sim in leader.simInfos:
                    if sim.id and not sim.isSelf: allRelIds.add(sim.id)

            if allRelIds:
                qargs = ','.join(['?' for _ in allRelIds])
                cursor.execute(f"SELECT * FROM assets WHERE id IN ({qargs})", list(allRelIds))

                relatMap = {}
                for row in cursor.fetchall():
                    relAsset = models.Asset.fromDB(cursor, row)
                    relatMap[relAsset.id] = relAsset

                for leader in leaders:
                    seen = {leader.id}
                    ldrSimIds = {s.id for s in leader.simInfos if s.id}

                    for sim in leader.simInfos:
                        if not sim.id or sim.id not in relatMap or sim.id in seen: continue

                        relAsset = relatMap[sim.id]
                        relSimIds = {s.id for s in relAsset.simInfos if s.id}

                        if len(relSimIds) == 1 and leader.id in relSimIds: continue

                        if relSimIds == ldrSimIds: continue

                        leader.relats.append(relAsset)
                        seen.add(sim.id)

            return leaders
    except Exception as e:
        lg.error(f"Error fetching assets: {str(e)}")
        return []
