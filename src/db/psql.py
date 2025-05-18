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

    def rmPrefixUpload(path):
        if path.startswith('upload/'): return path[7:]
        return path


    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        inPct = 0
        if onUpdate: onUpdate(inPct, f"{inPct}%", "Start query...")

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cntSql = "Select Count( * ) From assets Where type = %s"
        cntArs = [asType]

        if usrId:
            cntSql += " AND \"ownerId\" = %s"
            cntArs.append(usrId)

        cursor.execute(cntSql, cntArs)
        cntAll = cursor.fetchone()[0]

        lg.info(f"Found {cntAll} {asType.lower()} assets...")

        if onUpdate:
            inPct = 5
            onUpdate(inPct, f"{inPct}%", f"found {cntAll} ({asType.lower()}) assets...")

        sql = """
		  Select a.*, e.*
		  From assets a
					   Left Join exif e On a.id = e."assetId"
		  Where a.type = %s
              """

        params = [asType]

        if usrId:
            sql += " AND a.\"ownerId\" = %s"
            params.append(usrId)

        sql += " ORDER BY a.\"createdAt\" DESC"

        cursor.execute(sql, params)

        # API-compatible EXIF field list (based on API return results)
        api_exif_fields = [
            'make', 'model', 'exifImageWidth', 'exifImageHeight',
            'fileSizeInByte', 'orientation', 'dateTimeOriginal', 'modifyDate',
            'timeZone', 'lensModel', 'fNumber', 'focalLength', 'iso', 'exposureTime',
            'latitude', 'longitude', 'city', 'state', 'country',
            'description', 'projectionType', 'rating'
        ]

        # All possible EXIF field names (including fields not used by API)
        all_exif_fields = api_exif_fields + [
            'fps', 'livePhotoCID', 'profileDescription', 'colorspace',
            'bitsPerSample', 'autoStackId'
        ]

        baseFetchPct = 40

        if onUpdate:
            inPct = 10
            onUpdate(inPct, f"{inPct}%", "start reading...")

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

                exifInfo = {}

                for fd in api_exif_fields:
                    if fd in asset and asset[fd] is not None:
                        if fd in ('dateTimeOriginal', 'modifyDate'):
                            if isinstance(asset[fd], str):
                                exifInfo[fd] = asset[fd]
                            else:
                                exifInfo[fd] = asset[fd].isoformat() if asset[fd] else None
                        else:
                            exifInfo[fd] = asset[fd]

                # Remove all EXIF fields from asset dictionary
                for fd in all_exif_fields:
                    # If the field is 'description', only delete it if it's not empty
                    # because the assets table also has a description field
                    if fd != 'description' or (fd == 'description' and asset.get(fd) is not None):
                        asset.pop(fd, None)

                if exifInfo: asset['exifInfo'] = exifInfo

                assets.append(asset)

            if onUpdate and cntAll > 0:
                curPct = inPct + int(cntFetched / cntAll * (baseFetchPct - inPct))

                if cntFetched > 0:
                    tElapsed = time.time() - tStart
                    tPerItem = tElapsed / cntFetched
                    remainCnt = cntAll - cntFetched
                    remainTime = tPerItem * remainCnt
                    remainMins = int(remainTime / 60)
                    timeSuffix = f"remain: {remainMins} mins"
                else:
                    timeSuffix = "calcuating..."

                onUpdate(curPct, f"{curPct}%", f"processed {cntFetched}/{cntAll} ... {timeSuffix}")

        cursor.close()

        if onUpdate:
            curPct = baseFetchPct
            onUpdate(curPct, f"{curPct}%", "main assets done... query for files..")

        # get thumbnail and preview paths for each asset
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        flsSql = """
			   Select "assetId", type, path
			   From asset_files
			   Where "assetId" In %s
                   """

        assetIds = [a['id'] for a in assets]
        afs = []

        pathFetchPct = 40
        nextPct = baseFetchPct

        for idx, i in enumerate(range(0, len(assetIds), szChunk)):
            chunk = assetIds[i:i + szChunk]
            cursor.execute(flsSql, (tuple(chunk),))
            chunkResults = cursor.fetchall()
            afs.extend(chunkResults)

            if onUpdate and len(assetIds) > 0:
                chunkPct = min((idx + 1) * szChunk, len(assetIds))
                curPct = baseFetchPct + int(chunkPct / len(assetIds) * pathFetchPct)
                onUpdate(curPct, f"{curPct}%", f"query files.. {chunkPct}/{len(assetIds)}...")

        if onUpdate:
            nextPct = baseFetchPct + pathFetchPct
            onUpdate(nextPct, f"{nextPct}%", "files ready, combine data...")

        # Create a lookup dictionary for fast access
        dictFiles = {}
        for af in afs:
            assetId = af['assetId']
            typ = af['type']
            path = af['path']
            if assetId not in dictFiles: dictFiles[assetId] = {}
            dictFiles[assetId][typ] = path

        # Add path information to each asset
        finalPct = 20
        processedCount = 0

        for asset in assets:
            assetId = asset['id']
            if assetId in dictFiles:
                for typ, path in dictFiles[assetId].items():
                    if typ == Ks.db.thumbnail: asset['thumbnail_path'] = rmPrefixUpload(path)
                    elif typ == Ks.db.preview: asset['preview_path'] = rmPrefixUpload(path)

            asset['fullsize_path'] = rmPrefixUpload(asset.get('originalPath', ''))

            processedCount += 1

            if onUpdate and len(assets) > 0 and (processedCount % 100 == 0 or processedCount == len(assets)):
                curPct = nextPct + int(processedCount / len(assets) * finalPct)
                onUpdate(curPct, f"{curPct}%", f"processing {processedCount}/{len(assets)}...")

        cursor.close()

        lg.info(f"Successfully fetched {len(assets)} {asType.lower()} assets")

        if onUpdate:
            onUpdate(100, "100%", f"Complete Assets[{len(assets)}] ({asType.lower()})")

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
