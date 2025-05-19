import requests

from conf import envs, Ks
from util import log

lg = log.get(__name__)

#================================================================
# about api
#
# Because using the API requires you to record all users API keys
# and the API key is only displayed once when it's generated
# This causes some inconvenience for our usage
# So currently the API module is not being used
#================================================================


assets = []
timeout = 5000
urlApi:str = envs.immichUrl

if not urlApi.endswith('/'): urlApi += '/'
if not urlApi.endswith('api'): urlApi = urlApi + 'api'


if not urlApi: raise KeyError('[api] the urlApi environment variable is not set')

def _get(endpoint: str, apiKey: str, headers=None, params=None, stream=False):
    if not apiKey: raise KeyError('muse have ApiKey')

    if headers is None: headers = {}

    headers['x-api-key'] = apiKey
    if 'Accept' not in headers: headers['Accept'] = 'application/json'

    url = f"{urlApi}/{endpoint.lstrip('/')}"
    try:
        lg.info(f"[API] GET: url[{url}] header[{headers}]")
        rep = requests.get(url, headers=headers, params=params, verify=False, timeout=timeout, stream=stream)
        rep.raise_for_status()
        return rep
    except requests.exceptions.RequestException as e:
        lg.error(f"API GET request failed: {str(e)}")
        return None
    except Exception as e:
        lg.error(f"Unexpected error in API GET: {str(e)}")
        return None


def _post(endpoint: str, apiKey: str, data=None, json_data=None, headers=None):
    if not apiKey: raise KeyError('muse have ApiKey')
    if headers is None: headers = {}

    headers['x-api-key'] = apiKey
    if 'Accept' not in headers:
        headers['Accept'] = 'application/json'

    if json_data is not None and 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json'

    url = f"{urlApi}/{endpoint.lstrip('/')}"
    try:
        lg.debug(f"POST: {url}")
        rep = requests.post(url, headers=headers, data=data, json=json_data, verify=False, timeout=timeout)
        rep.raise_for_status()
        return rep
    except requests.exceptions.RequestException as e:
        lg.error(f"API POST request failed: {str(e)}")
        return None
    except Exception as e:
        lg.error(f"Unexpected error in API POST: {str(e)}")
        return None


def _api_delete(endpoint: str, apiKey: str, json_data=None, headers=None):
    if not apiKey: raise KeyError('muse have ApiKey')
    if headers is None: headers = {}

    headers['x-api-key'] = apiKey
    if json_data is not None and 'Content-Type' not in headers: headers['Content-Type'] = 'application/json'

    url = f"{urlApi}/{endpoint.lstrip('/')}"
    try:
        lg.debug(f"DELETE: {url}")
        rep = requests.delete(url, headers=headers, json=json_data, verify=False, timeout=timeout)
        rep.raise_for_status()
        return rep
    except requests.exceptions.RequestException as e:
        lg.error(f"API DELETE request failed: {str(e)}")
        return None
    except Exception as e:
        lg.error(f"Unexpected error in API DELETE: {str(e)}")
        return None


# 獲取圖片URL路徑，用於前端直接引用
def get_image_url(asset_id, quality=Ks.db.thumbnail):
    return f"/api/image/{asset_id}?quality={quality}"



# def fetchAssets(apiKey, fetchType="IMAGE"):
#     global assets
#     assets = []
#
#     urlAssetPath = "view/folder/unique-paths"
#     urlAssetDir = "view/folder"
#
#     try:
#         rep = _get(urlAssetPath, apiKey)
#         if not rep: raise RuntimeError("Failed to fetch asset paths")
#
#         content_type = rep.headers.get('Content-Type', '')
#         if 'application/json' in content_type and rep.text:
#             paths = rep.json()
#         else:
#             raise RuntimeError(f"Unexpected response: {content_type} / {rep.text[:100]}")
#
#         for path in paths:
#             if not path: continue
#
#             rep2 = _get(f"{urlAssetDir}?path={path}", apiKey)
#             if not rep2:
#                 lg.error(f"Failed to fetch assets for path: {path}")
#                 continue
#
#             try:
#                 path_assets = rep2.json()
#                 if path_assets: assets.extend(path_assets)
#             except Exception as e:
#                 lg.error(f"Failed to parse assets for path {path}: {str(e)}")
#                 continue
#
#         lg.debug(f"Total assets before filtering: {len(assets)}")
#         if assets:
#             sample_types = [a.get("type") for a in assets][:10]
#             lg.debug(f"Sample asset types: {sample_types}")
#
#         filtered_assets = [a for a in assets if a.get("type") == fetchType]
#         lg.info(f"Assets after filtering by type '{fetchType}': {len(filtered_assets)}")
#
#         if not filtered_assets:
#             lg.error("No assets found via API")
#             return []
#
#         return filtered_assets
#     except requests.exceptions.RequestException as e:
#         lg.error(f"API request failed: {str(e)}")
#         return []
#     except Exception as e:
#         lg.error(f"Failed to FetchAssets: {str(e)}")
#         return []

# Single API asset structure:
# {
#   "id": "e97e7882-b74a-48a1-aeaf-ca1d9e7a77cd",
#   "deviceAssetId": "./photos/20220214_164607.jpg-1644828367.0",
#   "ownerId": "85d32b71-4068-45e8-bd25-22e629d50388",
#   "deviceId": "python-uploader",
#   "libraryId": null,
#   "type": "IMAGE",
#   "originalPath": "upload/library/zz/2022/02/20220214_164607.jpg",
#   "originalFileName": "20220214_164607.jpg",
#   "originalMimeType": "image/jpeg",
#   "thumbhash": "YCgKDIKGKDdZWGdwiJegdEAiCA==",
#   "fileCreatedAt": "2022-02-14T08:46:07.000Z",
#   "fileModifiedAt": "2022-02-14T08:46:07.000Z",
#   "localDateTime": "2022-02-14T08:46:07.000Z",
#   "updatedAt": "2025-05-01T16:50:07.044Z",
#   "isFavorite": false,
#   "isArchived": false,
#   "isTrashed": false,
#   "duration": "0:00:00.00000",
#   "exifInfo": {
#     "make": null,
#     "model": null,
#     "exifImageWidth": 1700,
#     "exifImageHeight": 956,
#     "fileSizeInByte": 384977,
#     "orientation": null,
#     "dateTimeOriginal": "2022-02-14T08:46:07+00:00",
#     "modifyDate": "2022-02-14T08:46:07+00:00",
#     "timeZone": null,
#     "lensModel": null,
#     "fNumber": null,
#     "focalLength": null,
#     "iso": null,
#     "exposureTime": null,
#     "latitude": null,
#     "longitude": null,
#     "city": null,
#     "state": null,
#     "country": null,
#     "description": "",
#     "projectionType": null,
#     "rating": null
#   },
#   "livePhotoVideoId": null,
#   "people": [],
#   "checksum": "GZO1ZMUEfUgC1mvWUt3tDYbbgNE=",
#   "isOffline": false,
#   "hasMetadata": true,
#   "duplicateId": null,
#   "resized": true
# }


# def getImage(apiKey, assetId, photoQ=Ks.db.thumbnail):
#
#     lg.info( f"[getImage] Fetching asset: [{assetId}] apiKey[{apiKey}]" )
#
#     headers = {'Accept': 'application/octet-stream'}
#     rep = _get(f"assets/{assetId}/thumbnail?size={photoQ}", apiKey, headers=headers, stream=True)
#
#     if not rep:
#         lg.error(f"Failed to get image (id={assetId}, quality={photoQ})")
#         return None
#
#     if rep.status_code == 200 and 'image/' in rep.headers.get('Content-Type', ''):
#         try:
#             img = Image.open(BytesIO(rep.content))
#             img.load()
#             return img
#         except Exception as e:
#             lg.error(f"Failed to process image (id={assetId}, quality={photoQ}): {str(e)}")
#             return None
#     else:
#         lg.error(
#             f"Skipping non-image asset {assetId}: "
#             f"Content-Type: {rep.headers.get('Content-Type')}, "
#             f"Status code: {rep.status_code}"
#         )
#         return None
#
#
# def deleteAsset(apiKey, assetId):
#     payload = {"force": True, "ids": [assetId]}
#     rep = _api_delete("assets", apiKey, json_data=payload)
#     if not rep:
#         lg.error(f"Failed to delete asset {assetId}")
#         return False
#
#     code = rep.status_code
#     isOk = code == 204
#     if not isOk:
#         lg.error(f"assets deletion failed with status code {code}")
#
#     return isOk
