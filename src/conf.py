import os
import dotenv
import torch

# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

dotenv.load_dotenv()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def isInDocker(): return os.path.exists('/.dockerenv')

pathRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def pathFromRoot(path):
    if os.path.isabs(path): return path
    joined_path = os.path.join(pathRoot, path)
    return os.path.normpath(joined_path)

class envs:
    isDev = False if isInDocker() else os.getenv('IsDev')
    qdrantUrl = 'http://qdrant:6333' if isInDocker() else os.getenv('QDRANT_URL')
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
        mkitData = 'data/' if isInDocker() else os.getenv('MKIT_DATA', os.path.join(pathRoot, 'data/'))

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
        thMarks = { 0: "0", 0.2: "0.2", 0.4: "0.4", 0.6: "0.6", 0.8: "0.8", 0.9: "0.9", 0.95: "0.95", 1: "1" }

    class css:
        show = {"display": ""}
        hide = {"display": "none"}


if not envs.mkitData.endswith('/'): envs.mkitData = envs.mkitData + '/'

pathCache = envs.mkitData + 'cache/'
