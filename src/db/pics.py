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

            lg.info(f"[pics] db connected: {pathDb}")

        return True
    except Exception as e:
        raise mkErr("Failed to initialize pics database", e)

def clearAll():
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Drop Table If Exists assets")
            c.execute("Drop Table If Exists users")
            conn.commit()
        return init()
    except Exception as e:
        raise mkErr("Failed to clear pics database", e)


def clearBy(usrId):
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = "Delete From assets WHERE ownerId = ?"
            c.execute(sql, (usrId,))
            cnt = c.rowcount
            conn.commit()

            lg.info(f"[pics] delete userId[ {usrId} ] assets[ {cnt} ]")
            return cnt
    except Exception as e:
        raise mkErr(f"Failed to delete assets by userId[{usrId}]", e)


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
        raise mkErr("Failed to get assets count", e)


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
        raise mkErr("Failed to get asset by autoId", e)

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
        raise mkErr("Failed to get asset by id", e)

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
        raise mkErr(f"Failed to get assets by userId[{usrId}]", e)

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
        raise mkErr(f"Failed to get assets by ids[{ids}]", e)


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
        raise mkErr("Failed to get all assets", e)


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
        raise mkErr("Failed to get non-vector assets", e)

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

def setVectoredBy(asset: models.Asset, done=1, cur: Cursor = None):
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
        raise mkErr(f"Failed to update vector status for asset[{asset.id}]", e)

def saveBy(asset: dict, c: Cursor):  #, onExist:Callable[[models.Asset],None]):
    try:
        assId = asset.get('id', None)
        if not assId: return False

        if not isinstance(assId, str): assId = str(assId)

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
                localDateTime, thumbnail_path, preview_path, fullsize_path, jsonExif)
                Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(assId),
                str(asset.get('ownerId')),
                asset.get('deviceId'),
                asset.get('type'),
                asset.get('originalFileName'),
                asset.get('fileCreatedAt'),
                asset.get('fileModifiedAt'),
                1 if asset.get('isFavorite') else 0,
                1 if asset.get('isVisible') else 0,
                1 if asset.get('isArchived') else 0,
                asset.get('localDateTime'),
                asset.get('thumbnail_path'),
                asset.get('preview_path'),
                asset.get('fullsize_path', asset.get('originalPath')),
                jsonExif,
            ))

            return True

        return False  # ignore duplicates
    except Exception as e:
        raise mkErr("Failed to save asset", e)


#========================================================================
# sim
#========================================================================

def getAnyNonSim() -> Optional[models.Asset]:
    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("Select * From assets Where isVectored = 1 AND simOk!=1 AND json_array_length(simINfos) = 0")
            row = c.fetchone()
            if row is None: return None
            asset = models.Asset.fromDB(c, row)
            return asset
    except Exception as e:
        raise mkErr("Failed to get non-sim asset", e)

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


def setSimIds(assId: str, infos: List[models.SimInfo], isOk = 0, GID:Optional[int] = 0):
    if not infos or len(infos) <= 0:
        raise RuntimeError(f"Can't setSimIds id[{assId}] by [{type(infos)}], {tracebk.format_exc()}")

    try:
        with mkConn() as conn:
            c = conn.cursor()

            try:
                dictSimInfos = [sim.toDict() for sim in infos] if infos else []
                sqlGID = GID if GID else 0
                c.execute("UPDATE assets SET simOk = ?, simInfos = ?, simGID = ? WHERE id = ?", (isOk, json.dumps(dictSimInfos), sqlGID, assId))

                if not c.rowcount:
                    raise RuntimeError(f"No asset found with id: {assId}")

                conn.commit()
                lg.info(f"[pics] Updated assId[{assId}] simOK[{isOk}] simInfo[{len(infos)}] GID[{GID}]")

            except Exception as e:
                raise e
    except Exception as e:
        raise mkErr("Failed to set similar IDs", e)


def deleteBy(assets: List[models.Asset]):
    try:
        cntAll = len(assets)
        with mkConn() as conn:
            c = conn.cursor()
            assIds = [ass.id for ass in assets]
            gids = [ass.simGID for ass in assets]

            if not assIds or not gids: raise RuntimeError(f"No asset IDs found")

            qargs = ','.join(['?' for _ in assIds])
            c.execute(f"DELETE FROM assets WHERE id IN ({qargs})", assIds)
            count = c.rowcount

            if count != cntAll:
                raise mkErr(f"Failed to delete assets({cntAll}) with affected[{count}]")

            # reset same gid
            c.execute(f"UPDATE assets SET simGID = 0, simInfos= '[]' WHERE simOk = 0 AND simGID IN ({qargs})", gids)


            lg.info(f"[pics] delete by assIds[{cntAll}] rst[{count}]")

            # Delete vectors from Qdrant
            if assIds:
                import db.vecs as vecs
                vecs.deleteBy(assIds)

            conn.commit()

            return count
    except Exception as e:
        raise mkErr("Failed to delete assets", e)

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
        raise mkErr("Failed to resolve sim assets", e)

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
        raise mkErr("Failed to clear all sim results", e)


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
        raise mkErr(f"Failed to count assets with simInfos and simOk[{isOk}]", e)


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

def clearAllVectored():
    try:
        with mkConn() as cnn:
            c = cnn.cursor()
            c.execute("""
                UPDATE assets 
                SET isVectored=0
            """)
            cnn.commit()
    except Exception as e:
        raise mkErr(f"Failed to set isVectored to 0", e)

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
        raise mkErr(f"Failed execute SimAutoMark", e)




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


# 如果incGroup, 就帶入simGID相同的, 否則只帶入simInfos的
def getSimAssets(assId: str, incGroup = False) -> Optional[List[models.Asset]]:
    import numpy as np
    from db import vecs

    try:
        with mkConn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM assets WHERE id = ?", (assId,))
            row = c.fetchone()
            if row is None:
                lg.warn(f"[pics] SimGroup Root asset {assId} not found")
                return None

            root = models.Asset.fromDB(c, row)
            rst = [root]

            if not incGroup:
                if not root.simInfos or len(root.simInfos) <= 1: return rst

                simIds = [info.id for info in root.simInfos]
                if not simIds: return [root]

                qargs = ','.join(['?' for _ in simIds])
                c.execute(f"SELECT * FROM assets WHERE id IN ({qargs})", simIds)

                rows = c.fetchall()

                assets = [models.Asset.fromDB(c, row) for row in rows]

                for asset in assets:
                    asset.view.score = next( (info.score for info in root.simInfos if info.id == asset.id), 0 ) #理論上不應該空值

                assetMap = {asset.id: asset for asset in assets}

                sortAss = []
                for simInfo in sorted(root.simInfos, key=lambda x: x.score or 0, reverse=True):
                    if simInfo.id in assetMap:
                        sortAss.append(assetMap[simInfo.id])

                rst.extend(sortAss)
            else:
                if not root.simGID: return rst

                c.execute("SELECT * FROM assets WHERE simGID = ? AND id != ?", (root.simGID, assId))
                rows = c.fetchall()

                if not rows: return rst

                assets = [models.Asset.fromDB(c, row) for row in rows]

                try:
                    rootVec = vecs.getBy(assId)
                    rootVecNp = np.array(rootVec)

                    assScores = []
                    for ass in assets:
                        try:
                            assVec = vecs.getBy(ass.id)
                            assVecNp = np.array(assVec)
                            score = np.dot(rootVecNp, assVecNp)

                            ass.view.score = score

                            assScores.append((ass, score))
                        except Exception as e:
                            lg.warn(f"[pics] Failed to get vector for asset {ass.id}: {str(e)}")
                            continue

                    assScores.sort(key=lambda x: x[1], reverse=True)
                    rst.extend([ass for ass, _ in assScores])

                except Exception as e:
                    lg.error(f"[pics] Error processing vectors: {str(e)}")
                    rst.extend(assets)

            return rst
    except Exception as e:
        raise mkErr(f"Failed to get similar group for root {assId}", e)





# select have simInfos and simInfos not only isSelf
def countSimPending():
    try:
        with mkConn() as conn:
            c = conn.cursor()
            sql = '''
                WITH grpReps AS (
                    SELECT simGID, MIN(autoId) as repAutoId
                    FROM assets
                    WHERE simOk = 0 AND json_array_length(simInfos) > 1 AND simGID != 0
                    GROUP BY simGID
                )
                SELECT COUNT(*) FROM (
                    SELECT a.autoId FROM assets a
                    LEFT JOIN grpReps g ON a.simGID = g.simGID
                    WHERE a.simOk = 0 AND json_array_length(a.simInfos) > 1
                    AND (
                        (a.simGID = 0) OR 
                        (a.simGID != 0 AND a.autoId = g.repAutoId)
                    )
                )
            '''
            c.execute(sql)
            cnt = c.fetchone()[0]
            return cnt
    except Exception as e:
        raise mkErr(f"Failed to count assets pending", e)


def getPagedPending(page=1, size=20) -> list[models.Asset]:
    try:
        sql = '''
            WITH grpReps AS (
                SELECT simGID, MIN(autoId) as repAutoId
                FROM assets
                WHERE simOk = 0 AND json_array_length(simInfos) > 1 AND simGID != 0
                GROUP BY simGID
            )
            SELECT a.* FROM assets a
            LEFT JOIN grpReps g ON a.simGID = g.simGID
            WHERE a.simOk = 0 AND json_array_length(a.simInfos) > 1
            AND (
                (a.simGID = 0) OR 
                (a.simGID != 0 AND a.autoId = g.repAutoId)
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

            leader.relats = len(allRelIds)

            return leaders
    except Exception as e:
        lg.error(f"Error fetching assets: {str(e)}")
        return []
