
from typing import Optional
import traceback
import psycopg2
import psycopg2.extras
from conf import Ks, envs
from util import log

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


def fetchAssets(usrId, asType="IMAGE"):

    def rmPrefixUpload(path):
        if path.startswith('upload/'): return path[7:]
        return path


    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cntSql = "Select Count( * ) From assets Where type = %s"
        cntArs = [asType]

        if usrId:
            cntSql += " AND \"ownerId\" = %s"
            cntArs.append(usrId)

        cursor.execute(cntSql, cntArs)
        cntAll = cursor.fetchone()[0]

        lg.info(f"Found {cntAll} {asType.lower()} assets...")

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

        # FetchAssets in batches to avoid memory issues
        szBatch = 500
        assets = []
        cntFetched = 0

        while True:
            batch = cursor.fetchmany(szBatch)
            if not batch: break

            cntFetched += len(batch)

            for row in batch:
                asset = {key: row[key] for key in row.keys()}

                # Create exifInfo dictionary
                exifInfo = {}

                # Extract EXIF data (only keep API-compatible fields)
                for fd in api_exif_fields:
                    if fd in asset and asset[fd] is not None:
                        # For datetime fields, convert to string
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

                # Only add exifInfo to asset dictionary if it's not empty
                if exifInfo:
                    asset['exifInfo'] = exifInfo

                assets.append(asset)

        cursor.close()

        # get thumbnail and preview paths for each asset
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        flsSql = """
				   Select "assetId", type, path
				   From asset_files
				   Where "assetId" In %s
                   """

        assetIds = [a['id'] for a in assets]
        # Split into chunks of 1000 to avoid "too many parameters" error
        szChunk = 500
        afs = []

        for idx in range(0, len(assetIds), szChunk):
            chunk = assetIds[idx:idx + szChunk]
            cursor.execute(flsSql, (tuple(chunk),))
            afs.extend(cursor.fetchall())

        # Create a lookup dictionary for fast access
        dictFiles = {}
        for af in afs:
            assetId = af['assetId']
            typ = af['type']
            path = af['path']
            if assetId not in dictFiles: dictFiles[assetId] = {}
            dictFiles[assetId][typ] = path

        # Add path information to each asset
        for asset in assets:
            assetId = asset['id']
            if assetId in dictFiles:
                for typ, path in dictFiles[assetId].items():
                    if typ == Ks.db.thumbnail: asset['thumbnail_path'] = rmPrefixUpload(path)
                    elif typ == Ks.db.preview: asset['preview_path'] = rmPrefixUpload(path)

            # Convert to fullsize_path, because we use originalPath locally
            asset['fullsize_path'] = rmPrefixUpload(asset.get('originalPath', ''))

        cursor.close()

        lg.info(f"Successfully fetched {len(assets)} {asType.lower()} assets")

        return assets
    except Exception as e:
        lg.error(f"Failed to FetchAssets: {str(e)}")
        lg.info(traceback.format_exc())
        return []


def countAssets(usrId, assetType="IMAGE"):

    try:
        if not conn: raise RuntimeError("Failed to connect to psql")

        cursor = conn.cursor()

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
