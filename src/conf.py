import os
import dotenv
import torch

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

dotenv.load_dotenv()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def isInDocker(): return os.path.exists('/.dockerenv')

_pathBase = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class envs:
    qdrantUrl = 'http://qdrant:6333' if isInDocker() else os.getenv('QDRANT_URL')
    psqlHost = os.getenv('PSQL_HOST')
    psqlPort = os.getenv('PSQL_PORT')
    psqlDb = os.getenv('PSQL_DB')
    psqlUser = os.getenv('PSQL_USER')
    psqlPass = os.getenv('PSQL_PASS')
    immichUrl = os.getenv('IMMICH_URL')
    immichPath = os.getenv('IMMICH_PATH')
    mkitPort = os.getenv('MKIT_PORT', '8086')

    if os.getcwd().startswith(os.path.join(_pathBase, 'tests')):
        mkitData = os.path.join(_pathBase, 'data/')
    else:
        mkitData = 'data/' if isInDocker() else os.getenv('MKIT_DATA', os.path.join(_pathBase, 'data/'))

class Ks:
    title = "Immich-MediaKit"

    class pgs:
        fetch = 'fetch'
        photoVec = 'photoVec'
        settings = 'settings'
        similar = 'similar'
        viewGrid = 'viewGrid'

    class db:
        thumbnail = 'thumbnail'
        preview = 'preview'
        fullsize = 'original'

    class use:
        api = 'API'
        dir = 'DIR'

    class store:
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




if not envs.mkitData.endswith( '/' ): envs.mkitData = envs.mkitData + '/'


pathCache = envs.mkitData + 'cache/'
