import os
import time
from typing import Optional, List

import psycopg2
import psycopg2.extras

import imgs
from conf import ks, envs
from util import log
from mod import models
from util.err import mkErr

lg = log.get(__name__)


def init():
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        register_heif_opener = None
        lg.info("pillow-heif not available, skipping HEIC/HEIF support")

    host = envs.psqlHost
    port = envs.psqlPort
    db = envs.psqlDb
    uid = envs.psqlUser
    pw = envs.psqlPass

    if not all([host, port, db, uid]):
        raise RuntimeError("PostgreSQL connection settings not initialized.")

    try:
        conn = mkConn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        lg.error(f"PostgreSQL connection test failed: {str(e)}")
        return False


def mkConn():
    host = envs.psqlHost
    port = envs.psqlPort
    db = envs.psqlDb
    uid = envs.psqlUser
    pw = envs.psqlPass

    try:
        nc = psycopg2.connect(
            host=host,
            port=port,
            database=db,
            user=uid,
            password=pw
        )
        return nc
    except Exception as e:
        raise mkErr(f"Failed to connect to PostgreSQL", e)


def chk():
    conn = None
    try:
        conn = mkConn()
        c = conn.cursor()
        c.execute("SELECT 1")
        c.close()
        return True
    except Exception as e:
        raise mkErr(f"Failed to connect to PostgreSQL", e)
    finally:
        if conn: conn.close()


def fetchUser(usrId: str) -> Optional[models.Usr]:
    conn = None
    try:
        conn = mkConn()
        sql = """
        Select
            u.id,
            u.name,
            u.email
        From users u
        """
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(sql)
        row = cursor.fetchone()

        if row:
            return models.Usr.fromDict(dict(row))

        return None
    except Exception as e:
        raise mkErr(f"Failed to fetch userId[{usrId}]", e)

def fetchUsers() -> List[models.Usr]:
    conn = None
    try:
        conn = mkConn()
        sql = """
        Select
            u.id,
            u.name,
            u.email,
            a.key
        From users u
        Join api_keys a On u.id = a."userId"
        """
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(sql)
        dics = [dict(row) for row in cursor.fetchall()]
        users = [models.Usr.fromDict(d) for d in dics]

        return users
    except Exception as e:
        raise mkErr(f"Failed to fetch users", e)


def count(usrId=None, assetType="IMAGE"):
    conn = None
    try:
        conn = mkConn()
        cursor = conn.cursor()

        #lg.info( f"[psql] count userId[{usrId}]" )

        # noinspection SqlConstantExpression
        sql = "Select Count(*) From assets Where 1=1"
        params = []

        if assetType:
            sql += " AND type = %s"
            params.append(assetType)

        if usrId:
            sql += ' AND "ownerId" = %s'
            params.append(usrId)

        sql += " AND status = 'active'"

        cursor.execute(sql, params)
        count = cursor.fetchone()[0]
        cursor.close()

        #lg.info( f"[psql] count userId[{usrId}] rst[{count}]" )

        return count
    except Exception as e:
        raise mkErr(f"Failed to count assets", e)
    finally:
        if conn: conn.close()


# ------------------------------------------------------
# 因為db裡的值會帶upload/ (經由web上傳的)
# 要對應到真實路徑, 必需要把upload替換為實際路徑
# ------------------------------------------------------
def fixPrefix(path: Optional[str]):
    if path and path.startswith('upload/'): return path[7:]
    return path


def testAssetsPath():
    conn = None
    try:
        conn = mkConn()
        sql = "Select path From asset_files Limit 5"
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()

        isOk = False

        # lg.info( f"[psql] test AccessPath.. fetched: {len(rows)}" )

        if not rows or not len(rows): return "No Assets"

        for row in rows:
            path = row.get("path", None)
            if path:
                path = imgs.fixPath(fixPrefix(path))
                isOk = os.path.exists(path)
                # lg.info( f"[psql] test isOk[{isOk}] path: {path}" )
                if isOk:
                    return "OK"

            if not isOk: return f"{os.path.dirname(path)}"

        return f"test failed"

    except Exception as e:
        raise mkErr(f"Failed to test assets path", e)
    finally:
        if conn: conn.close()


#------------------------------------------------------------------------
# delete
#
# This function moves multiple assets to trash by updating their status to 'trashed' and setting deletedAt timestamp
# Note: This implementation follows Immich's API flow which may change in future versions
# follow delete flow
# https://github.com/immich-app/immich/blob/main/server/src/services/asset.service.ts#L231
#------------------------------------------------------------------------
def delete(asset: models.Asset):
    cnn = None
    try:
        if not asset or not asset.id: raise ValueError("Invalid asset or asset ID")

        cnn = mkConn()

        cursor = cnn.cursor()
        sql = """
        Update assets
        Set "deletedAt" = Now(), status = %s
        Where id = %s
        """
        cursor.execute(sql, (ks.db.status.trashed, asset.id))
        cnn.commit()
        cursor.close()

        return True
    except Exception as e:
        if cnn: cnn.rollback()
        raise mkErr(f"Failed to delete asset: {str(e)}", e)
    finally:
        if cnn: cnn.close()

def deleteBy(assetIds: List[str]):
    cnn = None
    try:
        if not assetIds or len(assetIds) <= 0: raise RuntimeError(f"can't delete assetIds empty {assetIds}")

        cnn = mkConn()
        cursor = cnn.cursor()
        sql = """
        Update assets
        Set "deletedAt" = Now(), status = %s
        Where id In %s
        """
        cursor.execute(sql, (ks.db.status.trashed, tuple(assetIds)))
        affectedRows = cursor.rowcount
        cnn.commit()
        cursor.close()

        return affectedRows
    except Exception as e:
        if cnn: cnn.rollback()
        raise mkErr(f"Failed to delete assets: {str(e)}", e)
    finally:
        if cnn: cnn.close()

#------------------------------------------------------------------------
# This function restores multiple assets from trash by updating their status back to 'active' and clearing deletedAt
# Note: This implementation follows Immich's API flow which may change in future versions
# restore flow
# https://github.com/immich-app/immich/blob/main/server/src/repositories/trash.repository.ts#L15
#------------------------------------------------------------------------
def restoreBy(assetIds: List[str]):
    cnn = None
    try:
        if not assetIds or len(assetIds) <= 0: raise RuntimeError(f"can't restore assetIds empty {assetIds}")

        cnn = mkConn()
        cursor = cnn.cursor()
        sql = """
        Update assets
        Set "deletedAt" = Null, status = %s
        Where id In %s And status = %s
        """
        cursor.execute(sql, (ks.db.status.active, tuple(assetIds), ks.db.status.trashed))
        affectedRows = cursor.rowcount
        cnn.commit()
        cursor.close()

        return affectedRows
    except Exception as e:
        if cnn: cnn.rollback()
        raise mkErr(f"Failed to restore assets: {str(e)}", e)
    finally:
        if cnn: cnn.close()


def fetchAssets(usr: models.Usr, asType="IMAGE", onUpdate: models.IFnProg = None):
    usrId = usr.id

    conn = None
    try:
        chk()

        onUpdate(11, f"start querying {usrId}")

        conn = mkConn()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # count all
        cntSql = "Select Count( * ) From assets Where status = 'active' And type = %s"
        cntArs = [asType]

        if usrId:
            cntSql += " AND \"ownerId\" = %s"
            cntArs.append(usrId)

        cursor.execute(cntSql, cntArs)
        cntAll = cursor.fetchone()[0]

        # lg.info(f"Found {cntAll} {asType.lower()} assets...")
        onUpdate(15, f"start querying {cntAll}")

        # ----------------------------------------------------------------
        # query assets
        # ----------------------------------------------------------------
        sql = "Select * From assets Where status = 'active' And type = %s"

        params = [asType]

        if usrId:
            sql += " AND \"ownerId\" = %s"
            params.append(usrId)

        sql += " ORDER BY \"createdAt\" DESC"

        cursor.execute(sql, params)

        szBatch = 100
        szChunk = 100
        assets = []
        cntFetched = 0

        tStart = time.time()

        while True:
            batch = cursor.fetchmany(szBatch)
            if not batch: break

            cntFetched += len(batch)

            for row in batch:
                asset = {key: row[key] for key in row.keys()}
                assets.append(asset)

            if cntAll > 0:
                if cntFetched > 0:
                    tmUsed = time.time() - tStart
                    tPerItem = tmUsed / cntFetched
                    remCnt = cntAll - cntFetched
                    remTime = tPerItem * remCnt
                    remMins = int(remTime / 60)
                    tmSuffix = f"remain: {remMins} mins"
                else:
                    tmSuffix = "calcuating..."

                # report("fetch", cntFetched, cntAll, f"processed {cntFetched}/{cntAll} ... {tmSuffix}")

        cursor.close()

        onUpdate(30, "main assets done... query for files..")

        # ----------------------------------------------------------------
        # query asset files
        # ----------------------------------------------------------------
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        flsSql = """
           Select "assetId", type, path
           From asset_files
           Where "assetId" In %s
        """

        assetIds = [a['id'] for a in assets]
        afs = []

        for idx, i in enumerate(range(0, len(assetIds), szChunk)):
            chunk = assetIds[i:i + szChunk]
            cursor.execute(flsSql, (tuple(chunk),))
            chunkResults = cursor.fetchall()
            afs.extend(chunkResults)

            chunkPct = min((idx + 1) * szChunk, len(assetIds))

        onUpdate(40, "files ready, combine data...")

        dictFiles = {}
        for af in afs:
            assetId = af['assetId']
            typ = af['type']
            path = af['path']
            if assetId not in dictFiles: dictFiles[assetId] = {}
            dictFiles[assetId][typ] = path

        # ----------------------------------------------------------------
        # query exif
        # ----------------------------------------------------------------
        exifSql = """
            Select *
            From exif
            Where "assetId" In %s
        """

        exifData = {}
        for idx, i in enumerate(range(0, len(assetIds), szChunk)):
            chunk = assetIds[i:i + szChunk]

            cursor.execute(exifSql, (tuple(chunk),))
            chunkResults = cursor.fetchall()

            for row in chunkResults:
                assetId = row['assetId']
                exifItem = {}

                for key, val in row.items():
                    if key == 'assetId': continue

                    if key in ('dateTimeOriginal', 'modifyDate') and val is not None:
                        if isinstance(val, str):
                            exifItem[key] = val
                        else:
                            exifItem[key] = val.isoformat() if val else None
                    elif val is not None:
                        exifItem[key] = val

                if exifItem:
                    exifData[assetId] = exifItem

            chunkPct = min((idx + 1) * szChunk, len(assetIds))

        # ----------------------------------------------------------------
        # combine & fetch thumbnail image
        # ----------------------------------------------------------------
        onUpdate(45, "files ready, combine data...")

        cntOk = 0
        cntErr = 0

        rstAssets = []

        for asset in assets:
            assetId = asset['id']
            if assetId in dictFiles:
                for typ, path in dictFiles[assetId].items():
                    if typ == ks.db.thumbnail: asset['thumbnail_path'] = fixPrefix(path)
                    elif typ == ks.db.preview: asset['preview_path'] = fixPrefix(path)

            asset['fullsize_path'] = fixPrefix(asset.get('originalPath', ''))

            if assetId in exifData:
                asset['exifInfo'] = exifData[assetId]
            else:
                lg.warn(f"[exif] NotFound.. assetId[{assetId}]")

            # final check
            pathThumbnail = asset.get('thumbnail_path')
            if not pathThumbnail:
                cntErr += 1
                lg.warn(f"[psql] ignore asset: {asset}")
                continue

            cntOk += 1
            rstAssets.append(asset)

            # if len(assets) > 0 and (cntOk % 100 == 0 or cntOk == len(assets)):
            #     report("combine", cntOk, len(assets), f"processing {cntOk}/{len(assets)}...")

        cursor.close()

        lg.info(f"Successfully fetched {len(rstAssets)} {asType.lower()} assets")
        onUpdate(5, f"Successfully fetched {len(rstAssets)} {asType.lower()} assets")

        return rstAssets
    except Exception as e:
        msg = f"Failed to FetchAssets: {str(e)}"
        raise mkErr(msg, e)
    finally:
        if conn: conn.close()
