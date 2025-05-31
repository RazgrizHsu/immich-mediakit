import os
from typing import Dict, Callable, Optional

import dotenv
import torch

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

dotenv.load_dotenv()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
pathRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
isDock = os.path.exists('/.dockerenv')


# ------------------------------------------------------------------------
# code helper
# ------------------------------------------------------------------------
class co:
    class to:
        @classmethod
        def dict(cls):
            return {key: value for key, value in vars(cls).items() if not key.startswith('_') and not callable(value)}


    class tit(str):
        name: str = ''
        desc: str = ''
        cmds: Dict[str, str] = None

        def __new__(cls, v='', name='', cmds: Dict[str, str] = None, desc='') -> 'co.tit':
            me = super().__new__(cls, v)
            me.name = name
            me.cmds = cmds
            me.desc = desc
            # noinspection PyTypeChecker
            return me

    class find:
        @classmethod
        def find(cls, key: str):
            for attr_name in dir(cls):
                if attr_name.startswith('__') or callable(getattr(cls, attr_name)): continue
                attr = getattr(cls, attr_name)
                if isinstance(attr, co.tit) and attr == key: return attr
            return None

        @classmethod
        def findBy(cls, key: str, value):
            for name in dir(cls):
                if name.startswith('__') or callable(getattr(cls, name)): continue
                obj = getattr(cls, name)
                if isinstance(obj, co.tit) and hasattr(obj, key):
                    if getattr(obj, key) == value: return obj
            return None

    class valid:
        @staticmethod
        def float(v, default, mi=0.01, mx=1):
            try:
                fv = float(v)
                if fv < mi or fv > mx: return default
                return fv
            except (ValueError, TypeError):
                return default

# ------------------------------------------------------------------------
# keys
# ------------------------------------------------------------------------
class cmds:
    class fetch(co.to):
        asset = co.tit('fetch_asset',desc='Fetch assets from remote')
        clear = co.tit('fetch_clear',desc='Clear select user assets and vectors')
        reset = co.tit('fetch_reset',desc='Clear all assets and vectors')

    class vec(co.to):
        toVec = co.tit('vec_toVec',desc='Generate vectors from assets')
        clear = co.tit('vec_clear',desc='Clear all vectors')

    class sim(co.to):
        fdSim = co.tit('sim_find', desc='Find Similar vectors')
        clear = co.tit('sim_clear', desc='Clear all similar results')
        selOk = co.tit('sim_selOk', desc='Reslove selected assets')
        selRm = co.tit('sim_selRm', desc='Delete selected assets')
        allOk = co.tit('sim_allOk', desc='Reslove All assets')
        allRm = co.tit('sim_allRm', desc='Delete All assets')

class ks:
    title = "Immich-MediaKit"
    cmd = cmds

    class pg(co.find):
        fetch = co.tit('fetch', 'FetchAssets', cmds.fetch.dict(), desc='Get photo asset from (Api/Psql) and save to local db')
        vector = co.tit('vector', 'ToVectors', cmds.vec.dict(), desc='Process photos to generate feature vectors for similarity calculations. This step reads each photo and generates a 2048-dimensional vector')
        similar = co.tit('similar', 'Similarity', cmds.sim.dict(), desc='Find similar photos based on image content. This uses AI-generated vector embeddings to find visually similar assets')
        system = co.tit('system', 'System', desc='display system settings')
        view = co.tit('view', 'View', desc='Use the filters and sorting options to customize your view')


    class db:
        thumbnail = 'thumbnail'
        preview = 'preview'
        fullsize = 'original'

        class status:
            trashed = 'trashed'
            active = 'active'
            deleted = 'deleted'

    class use:
        api = 'API'
        dir = 'DIR'

        class mth:
            cosine = co.tit('cosine', 'Cosine Similarity')
            euclid = co.tit('euclidean', 'Euclidean Distance')


    class sto:
        init = 'store-init'
        now = 'store-now'
        tsk = 'store-tsk'
        nfy = 'store-nfy'
        mdl = 'store-mdl'
        mdlImg = 'store-mdl-img'

        cnt = 'store-count'

    class defs:
        exif = {
            "dateTimeOriginal": "Capture Time",
            "modifyDate": "Modify Time",
            "make": "Camera Brand",
            "model": "Camera Model",
            "lensModel": "Lens",
            "fNumber": "Aperture",
            "focalLength": "Focal Length",
            "exposureTime": "Exposure Time",
            "iso": "ISO",
            "exifImageWidth": "Width",
            "exifImageHeight": "Height",
            "fileSizeInByte": "File Size",
            "orientation": "Orientation",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "city": "City",
            "state": "State",
            "country": "Country",
            "description": "Description",
            "fps": "Frame Rate",
            "livePhotoCID": "Live Photo CID",
            "timeZone": "Time Zone",
            "projectionType": "Projection Type",
            "profileDescription": "Profile Description",
            "colorspace": "Color Space",
            "bitsPerSample": "Bits Per Sample",
            "autoStackId": "Auto Stack ID",
            "rating": "Rating",
            "updatedAt": "Updated At",
            "updateId": "Update ID"
        }
        thMarks = {0.5:"0.5", 0.7: "0.7", 0.8: "0.8", 0.85:"0.85", 0.9: "0.9", 0.95: "0.95", 1: "1"}


    class css:
        show = {"display": ""}
        hide = {"display": "none"}


# ------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------
class url:
    @staticmethod
    def get_image_url(assetId, photoQ=ks.db.thumbnail):
        return f"/api/image/{assetId}?quality={photoQ}"

def pathFromRoot(path):
    if os.path.isabs(path): return path
    joined_path = os.path.join(pathRoot, path)
    return os.path.normpath(joined_path)

# ------------------------------------------------------------------------
# envs
# ------------------------------------------------------------------------
class envs:
    isDev = False if isDock else os.getenv('IsDev')
    isDock = False if not isDock else True
    immichPath = os.getenv('IMMICH_PATH')
    qdrantUrl = 'http://immich-mediakit-qdrant:6333' if isDock else os.getenv('QDRANT_URL')
    psqlHost = os.getenv('PSQL_HOST')
    psqlPort = os.getenv('PSQL_PORT')
    psqlDb = os.getenv('PSQL_DB')
    psqlUser = os.getenv('PSQL_USER')
    psqlPass = os.getenv('PSQL_PASS')
    mkitPort = os.getenv('MKIT_PORT', '8086')
    mkitPortWs = os.getenv('MIKT_PORTWS', '8087')

    if os.getcwd().startswith(os.path.join(pathRoot, 'tests')):
        mkitData = os.path.join(pathRoot, 'data/')
    else:
        mkitData = 'data/' if isDock else os.getenv('MKIT_DATA', os.path.join(pathRoot, 'data/'))
        if not mkitData.endswith('/'): mkitData += '/'

# ------------------------------------------------------------------------
# WebSocket URL generator
# ------------------------------------------------------------------------
def getWebSocketUrl():
    if isDock:
        return f"ws://localhost:{envs.mkitPortWs}"

    host = os.getenv('MKIT_WS_HOST', 'localhost')
    return f"ws://{host}:{envs.mkitPortWs}"

# ------------------------------------------------------------------------
# const
# ------------------------------------------------------------------------

pathCache = envs.mkitData + 'cache/'
