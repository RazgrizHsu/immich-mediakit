from typing import Optional
import traceback
import time
import psycopg2
import psycopg2.extras
from conf import Ks, envs
from util import log
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

    pgHost = envs.psqlHost
    pgPort = envs.psqlPort
    pgDB = envs.psqlDb
    pgUser = envs.psqlUser
    pgPass = envs.psqlPass
    pgImgPath = envs.immichPath

    if not (pgHost is not None and pgPort is not None and pgDB is not None and pgUser is not None):
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

    try:
        conn = psycopg2.connect(
            host=pgHost,
            port=pgPort,
            database=pgDB,
            user=pgUser,
            password=pgPass
        )
        return conn
    except Exception as e:
        lg.error(f"Failed to connect to PostgreSQL: {str(e)}")
        return None



def fetchUsers():
    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        sql = """
        Select
            u.id,
            u.name,
            u.email,
            a.key As apiKey
        From users u
        Join api_keys a On u.id = a."userId"
        """
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(sql)
        users = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return users
    except Exception as e:
        lg.error(f"Failed to fetch users: {str(e)}")
        lg.info(traceback.format_exc())
        return []


def fetchAssets(usrId, asType="IMAGE", onUpdate:IFnProg=None):
    from dataclasses import dataclass

    @dataclass
    class StageInfo:
        name: str
        base: int
        range: int

    #------------------------------------------------------
    # 因為db裡的值會帶upload/ (經由web上傳的)
    # 要對應到真實路徑, 必需要把upload替換為實際路徑
    #------------------------------------------------------
    def rmPrefixUpload(path):
        if path.startswith('upload/'): return path[7:]
        return path

    #------------------------------------------------------
    # 進度計算與回報的嵌套函數
    #------------------------------------------------------
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
            "init": StageInfo("初始化", 0, 5),
            "fetch": StageInfo("獲取資產", 5, 35),
            "files": StageInfo("獲取檔案", 40, 40),
            "exif": StageInfo("獲取EXIF", 80, 10),
            "combine": StageInfo("合併數據", 90, 10),
            "complete": StageInfo("完成", 100, 0)
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

        # query assets
        sql = "Select * From assets Where status = 'active' And type = %s"

        params = [asType]

        if usrId:
            sql += " AND a.\"ownerId\" = %s"
            params.append(usrId)

        sql += " ORDER BY a.\"createdAt\" DESC"

        cursor.execute(sql, params)

        upd("fetch", 0, cntAll, "start reading...", True)


        szBatch = 500
        szChunk = 500
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

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # query asset files
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

        upd("exif", 0, len(assetIds), "files ready, query exif data...", True)


        # query exif
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

        upd("exif", len(assetIds), len(assetIds), "exif ready, combine data...", True)

        processedCount = 0

        for asset in assets:
            assetId = asset['id']
            if assetId in dictFiles:
                for typ, path in dictFiles[assetId].items():
                    if typ == Ks.db.thumbnail: asset['thumbnail_path'] = rmPrefixUpload(path)
                    elif typ == Ks.db.preview: asset['preview_path'] = rmPrefixUpload(path)

            asset['fullsize_path'] = rmPrefixUpload(asset.get('originalPath', ''))

            if assetId in exifData: asset['exifInfo'] = exifData[assetId]

            processedCount += 1

            if len(assets) > 0 and (processedCount % 100 == 0 or processedCount == len(assets)):
                upd("combine", processedCount, len(assets), f"processing {processedCount}/{len(assets)}...")

        cursor.close()

        lg.info(f"Successfully fetched {len(assets)} {asType.lower()} assets")

        upd("complete", 1, 1, f"Complete Assets[{len(assets)}] ({asType.lower()})", True)

        return assets
    except Exception as e:
        lg.error(f"Failed to FetchAssets: {str(e)}")
        lg.info(traceback.format_exc())

        if onUpdate:
            onUpdate(100, "100%", f"fetch Assets failed: {str(e)}")

        return []


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
        lg.error(f"Failed to count assets: {str(e)}")
        lg.info(traceback.format_exc())
        return 0
