import os
import time
from typing import Optional, List

import psycopg2
import psycopg2.extras

import imgs
from conf import ks, envs
from util import log, models
from util.err import mkErr
from util.task import IFnProg

lg = log.get(__name__)

conn: Optional[psycopg2.extensions.connection] = None


def init():
    global conn
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()

    except ImportError:
        lg.info("pillow-heif not available, skipping HEIC/HEIF support")
        return False

    host = envs.psqlHost
    port = envs.psqlPort
    db = envs.psqlDb
    uid = envs.psqlUser
    pw = envs.psqlPass

    if not (host is not None and port is not None and db is not None and uid is not None):
        raise RuntimeError("PostgreSQL connection settings not initialized.")

    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            return conn
        except Exception as e:
            lg.info(f"Connection test failed: {str(e)}")
            conn = None
            connected = False

    conn = mkConn()
    return conn


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

def fetchUsers():
    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        sql = """
        Select
            u.id,
            u.name,
            u.email,
            a.key As ak 
        From users u
        Join api_keys a On u.id = a."userId"
        """
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(sql)
        users = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return users
    except Exception as e:
        raise mkErr(f"Failed to fetch users", e)


def count(usrId=None, assetType="IMAGE"):
    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        cursor = conn.cursor()

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

        return count
    except Exception as e:
        raise mkErr(f"Failed to count assets", e)


# ------------------------------------------------------
# 因為db裡的值會帶upload/ (經由web上傳的)
# 要對應到真實路徑, 必需要把upload替換為實際路徑
# ------------------------------------------------------
def fixPrefix(path: Optional[str]):
    if path and path.startswith('upload/'): return path[7:]
    return path


def testAssetsPath():
    if not conn: return f"pql not ready"

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

    if not isOk: return "Access Failed"

    return f"test failed"


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
# https://github.com/immich-app/immich/blob/main/server/src/controllers/trash.controller.ts
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


from dataclasses import dataclass

def fetchAssets(usr: models.Usr, asType="IMAGE", onUpdate: IFnProg = None):
    usrId = usr.id

    @dataclass
    class StageInfo:
        name: str
        base: int
        range: int

    # ------------------------------------------------------
    # report fn
    # ------------------------------------------------------
    def upd(sid, cnow, call, msg, force=False):
        if not onUpdate: return

        stg = stages.get(sid)
        if not stg: return

        if call <= 0:
            pct = stg.base
            onUpdate(pct, f"{pct}%", msg)
            return pct

        fraction = min(1.0, cnow / call)
        pct = stg.base + int(fraction * stg.range)

        if force or cnow == call or cnow % 100 == 0: onUpdate(pct, f"{pct}%", msg)

        return pct

    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        stages = {
            "init": StageInfo("init", 0, 5),
            "fetch": StageInfo("fetch db", 5, 35),
            "files": StageInfo("fetch assetFiels", 40, 40),
            "exif": StageInfo("fetch exif", 80, 10),
            "combine": StageInfo("combine", 90, 10),
            "complete": StageInfo("complete", 100, 0)
        }

        upd("init", 0, 1, "Start query...", True)

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # count all
        cntSql = "Select Count( * ) From assets Where status = 'active' And type = %s"
        cntArs = [asType]

        if usrId:
            cntSql += " AND \"ownerId\" = %s"
            cntArs.append(usrId)

        cursor.execute(cntSql, cntArs)
        cntAll = cursor.fetchone()[0]

        lg.info(f"Found {cntAll} {asType.lower()} assets...")

        upd("init", 1, 1, f"found {cntAll} ({asType.lower()}) assets...", True)

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

        upd("fetch", 0, cntAll, "start reading...", True)

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

                upd("fetch", cntFetched, cntAll, f"processed {cntFetched}/{cntAll} ... {tmSuffix}")

        cursor.close()

        upd("fetch", cntAll, cntAll, "main assets done... query for files..", True)

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
            upd("files", chunkPct, len(assetIds), f"query files.. {chunkPct}/{len(assetIds)}...")

        upd("files", len(assetIds), len(assetIds), "files ready, combine data...", True)

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
        upd("exif", 0, len(assetIds), "files ready, query exif data...", True)
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
            upd("exif", chunkPct, len(assetIds), f"query exif.. {chunkPct}/{len(assetIds)}...")

        # ----------------------------------------------------------------
        # combine & fetch thumbnail image
        # ----------------------------------------------------------------
        upd("exif", len(assetIds), len(assetIds), "exif ready, combine data...", True)

        processedCount = 0
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
                lg.warn( f"[psql] ignore asset: {asset}" )
                continue


            processedCount += 1
            rstAssets.append(asset)

            if len(assets) > 0 and (processedCount % 100 == 0 or processedCount == len(assets)):
                upd("combine", processedCount, len(assets), f"processing {processedCount}/{len(assets)}...")

        cursor.close()

        lg.info(f"Successfully fetched {len(rstAssets)} {asType.lower()} assets")

        upd("complete", 1, 1, f"Complete fetched Assets[{len(rstAssets)}] error[{cntErr}]", True)

        return rstAssets
    except Exception as e:
        msg = f"Failed to FetchAssets: {str(e)}"
        if onUpdate: onUpdate(100, "Erorr", msg)
        raise mkErr(msg, e)
