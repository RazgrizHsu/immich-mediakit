import json
import sqlite3
import traceback
from typing import Optional, List

from conf import envs
from util import log, models
from util.baseModel import BaseDictModel

lg = log.get(__name__)
conn: Optional[sqlite3.dbapi2.Connection] = None

def getConn():
    global conn
    pathDb = envs.mkitData + 'pics.db'
    if conn is None:
        conn = sqlite3.connect(pathDb, check_same_thread=False)
        lg.info(f"[pics] connected db: {pathDb}")
    return conn


def close():
    global conn
    try:
        if conn is not None: conn.close()
        conn = None
        return True
    except Exception as e:
        lg.error(f"Failed to close database connection: {str(e)}")
        return False


def init():
    global conn
    try:
        if conn is not None:
            conn.close()
            conn = None

        conn = getConn()
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
                isVectored       INTEGER Default 0,
                simOk            INTEGER Default 0,
                simIds           TEXT Default '[]'
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
        return True
    except Exception as e:
        lg.error(f"Failed to initialize duplicate photo database: {str(e)}")
        return False

def clear():
    try:
        if conn is not None:
            c = conn.cursor()

            c.execute("Drop Table If Exists assets")
            c.execute("Drop Table If Exists users")

            conn.commit()

        return init()
    except Exception as e:
        lg.error(f"Failed to clear database: {str(e)}")
        return False


def hasData(): return count() > 0


def count(usrId=None):
    try:
        if conn is None: raise RuntimeError('the db is not init')

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
        lg.error(f"Failed to get asset count: {str(e)}")
        return 0


def getAnyNonSim() -> Optional[models.Asset]:
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()
        c.execute("Select * From assets Where simOk!=1")

        row = c.fetchone()
        if row is None: return None

        asset = models.Asset.fromDB(c, row)
        return asset
    except Exception as e:
        lg.error(f"Failed to get asset information: {str(e)}")
        return None

def get(assetId) -> Optional[models.Asset]:
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()
        c.execute("Select * From assets Where id = ?", (assetId,))

        row = c.fetchone()
        if row is None: return None

        asset = models.Asset.fromDB(c, row)
        return asset
    except Exception as e:
        lg.error(f"Failed to get asset information: {str(e)}")
        return None


def getAll(count=0) -> list[models.Asset]:
    try:
        if conn is None: raise RuntimeError('the db is not init')

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
        lg.error(f"Failed to get all asset information: {str(e)}")
        return []


def getPaged(page=1, per_page=20, usrId=None) -> tuple[List[models.Asset], int]:
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()

        if usrId:
            c.execute("Select Count(*) From assets Where ownerId = ?", (usrId,))
        else:
            c.execute("Select Count(*) From assets")

        cnt = c.fetchone()[0]

        offset = (page - 1) * per_page

        if usrId:
            c.execute('''
                Select *
                From assets
                Where ownerId = ?
                Order By autoId Desc
                Limit ? Offset ?
                ''', (usrId, per_page, offset))
        else:
            c.execute('''
                Select *
                From assets
                Order By autoId Desc
                Limit ? Offset ?
                ''', (per_page, offset))

        rows = c.fetchall()
        if not rows: return [], cnt

        assets = [models.Asset.fromDB(c, row) for row in rows]
        return assets, cnt
    except Exception as e:
        lg.error(f"Failed to get paginated asset information: {str(e)}")
        return [], 0



def saveBy(asset: dict):
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()

        assetId = asset.get('id')
        if not assetId: return False

        exifInfo = asset.get('exifInfo', {})
        jsonExif = None
        if exifInfo:
            try:
                jsonExif = json.dumps(exifInfo, ensure_ascii=False, default=BaseDictModel.jsonSerializer)
                lg.info(f"json: {jsonExif}")
            except Exception as e:
                raise f"[pics.save] Error converting EXIF to JSON: {str(e)}"

        c.execute("Select autoId, id From assets Where id = ?", (assetId,))
        row = c.fetchone()

        if row is None:
            c.execute('''
                Insert Into assets (id, ownerId, deviceId, type, originalFileName,
                fileCreatedAt, fileModifiedAt, isFavorite, isVisible, isArchived,
                libraryId, localDateTime, thumbnail_path, preview_path, fullsize_path, jsonExif)
                Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assetId,
                asset.get('ownerId'),
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

        elif asset.get('thumbnail_path') or asset.get('preview_path') or asset.get('fullsize_path') or jsonExif:
            updFields = []
            updValues = []

            c.execute("Select thumbnail_path, preview_path, fullsize_path From assets Where id = ?", (assetId,))
            paths = c.fetchone()

            # If thumbnail path is provided and existing path is empty
            if asset.get('thumbnail_path') and (not paths or not paths[0]):
                updFields.append("thumbnail_path = ?")
                updValues.append(asset.get('thumbnail_path'))

            # If preview path is provided and existing path is empty
            if asset.get('preview_path') and (not paths or not paths[1]):
                updFields.append("preview_path = ?")
                updValues.append(asset.get('preview_path'))

            # If original path is provided and existing path is empty
            fullsize = asset.get('fullsize_path', asset.get('originalPath'))
            if fullsize and (not paths or not paths[2]):
                updFields.append("fullsize_path = ?")
                updValues.append(fullsize)

            # Check EXIF updates
            if jsonExif:
                c.execute("Select jsonExif From assets Where id = ?", (assetId,))
                existing_exif = c.fetchone()
                if not existing_exif or not existing_exif[0]:
                    updFields.append("jsonExif = ?")
                    updValues.append(jsonExif)

            if updFields:
                update_query = f"UPDATE assets SET {', '.join(updFields)} WHERE id = ?"
                updValues.append(assetId)
                c.execute(update_query, updValues)

        conn.commit()
        return True
    except Exception as e:
        lg.error(f"Failed to save asset information: {str(e)}")
        lg.error(traceback.format_exc())
        raise


def deleteForUsr(usrId):
    import db.vecs as vecs
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()

        c.execute("Select id From assets Where ownerId = ?", (usrId,))
        assetIds = [row[0] for row in c.fetchall()]

        lg.info(f"[pics] delete pics[{len(assetIds)}] for usrId[{usrId}]")

        c.execute("Delete From assets Where ownerId = ?", (usrId,))

        conn.commit()

        lg.info(f"[pics] delete vectors for usrId[{usrId}]")
        for assId in assetIds:
            vecs.deleteBy(assId)

        return True
    except Exception as e:
        lg.error(f"Failed to delete user assets: {str(e)}")
        return False




def setSimIds(assetId: str, similarIds: List[str]):
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()

        c.execute("SELECT id FROM assets WHERE id = ?", (assetId,))
        if not c.fetchone():
            lg.error(f"Asset {assetId} not found")
            return False

        c.execute("UPDATE assets SET simIds = ? WHERE id = ?", (json.dumps(similarIds), assetId))
        conn.commit()

        lg.info(f"Updated simIds for asset {assetId}: {len(similarIds)} similar assets")
        return True
    except Exception as e:
        lg.error(f"Failed to set similar IDs: {str(e)}")
        lg.error(traceback.format_exc())
        return False


def clearSimIds():
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()
        c.execute("UPDATE assets SET simOk = 0, simIds = '[]'")
        conn.commit()

        count = c.rowcount
        lg.info(f"Cleared similarity results for {count} assets")
        return True
    except Exception as e:
        lg.error(f"Failed to clear similarity results: {str(e)}")
        lg.error(traceback.format_exc())
        return False


def countSimOk(isOk=0):
    try:
        if conn is None: raise RuntimeError('the db is not init')

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM assets WHERE simOk = ?", (isOk,))
        count = c.fetchone()[0]

        return count
    except Exception as e:
        lg.error(f"Failed to count assets with simOk={isOk}: {str(e)}")
        lg.error(traceback.format_exc())
        return 0
