import os
from typing import Dict

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


    class title(str):
        name: str = ''
        desc: str = ''
        cmds: Dict[str, str] = None

        def __new__(cls, v='', name='', cmds: Dict[str, str] = None, desc='') -> 'co.title':
            me = super().__new__(cls, v)
            me.name = name
            me.cmds = cmds
            # noinspection PyTypeChecker
            return me

    class find:
        @classmethod
        def find(cls, key: str):
            for attr_name in dir(cls):
                if attr_name.startswith('__') or callable(getattr(cls, attr_name)): continue
                attr = getattr(cls, attr_name)
                if isinstance(attr, co.title) and attr == key: return attr
            return None

        @classmethod
        def findBy(cls, key: str, value):
            for name in dir(cls):
                if name.startswith('__') or callable(getattr(cls, name)): continue
                obj = getattr(cls, name)
                if isinstance(obj, co.title) and hasattr(obj, key):
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
        asset = 'fetch_asset'
        clear = 'fetch_clear'

    class vec(co.to):
        toVec = 'vec_toVec'
        clear = 'vec_clear'

    class sim(co.to):
        find = 'sim_find'
        clear = 'sim_clear'

class ks:
    title = "Immich-MediaKit"
    cmd = cmds

    class pg(co.find):
        fetch = co.title('fetch', 'FetchAssets', cmds.fetch.dict(), desc='Get photo asset from (Api/Psql) and save to local db')
        vec = co.title('photoVec', 'ToVectors', cmds.vec.dict(), desc='Process photos to generate feature vectors for similarity calculations. This step reads each photo and generates a 2048-dimensional vector')
        similar = co.title('similar', 'Similarity', cmds.sim.dict(), desc='Find similar photos based on image content. This uses AI-generated vector embeddings to find visually similar assets')
        settings = co.title('settings', 'Settings', desc='')
        viewGrid = co.title('viewGrid', 'ViewGrid', desc='')


    class db:
        thumbnail = 'thumbnail'
        preview = 'preview'
        fullsize = 'original'

    class use:
        api = 'API'
        dir = 'DIR'

    class sto:
        init = 'store-init'
        now = 'store-now'
        tsk = 'store-tsk'
        nfy = 'store-nfy'
        mdl = 'store-mdl'
        mdlImg = 'store-mdl-img'

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
            "fileSizeInByte": "File Size"
        }
        thMarks = {0: "0", 0.2: "0.2", 0.4: "0.4", 0.6: "0.6", 0.8: "0.8", 0.9: "0.9", 0.95: "0.95", 1: "1"}

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
    qdrantUrl = 'http://qdrant:6333' if isDock else os.getenv('QDRANT_URL')
    psqlHost = os.getenv('PSQL_HOST')
    psqlPort = os.getenv('PSQL_PORT')
    psqlDb = os.getenv('PSQL_DB')
    psqlUser = os.getenv('PSQL_USER')
    psqlPass = os.getenv('PSQL_PASS')
    immichUrl = os.getenv('IMMICH_URL')
    immichPath = os.getenv('IMMICH_PATH')
    mkitPort = os.getenv('MKIT_PORT', '8086')

    if os.getcwd().startswith(os.path.join(pathRoot, 'tests')):
        mkitData = os.path.join(pathRoot, 'data/')
    else:
        mkitData = 'data/' if isDock else os.getenv('MKIT_DATA', os.path.join(pathRoot, 'data/'))
        if not mkitData.endswith('/'): mkitData += '/'

# ------------------------------------------------------------------------
# const
# ------------------------------------------------------------------------

pathCache = envs.mkitData + 'cache/'
