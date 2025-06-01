import os
import time
import torch
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import threading

from typing import List, Optional, Tuple

import numpy as np
from torchvision.models import resnet152, ResNet152_Weights
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

os.environ['KMP_DUPLICATE_LIB_OK'] = "TRUE"

import db, conf
from util import log
from mod import models
from util.err import mkErr
from conf import envs


lg = log.get(__name__)

base_model = resnet152(weights=ResNet152_Weights.DEFAULT)

class FeatureExtractor(torch.nn.Module):
    def __init__(self, base_model):
        super(FeatureExtractor, self).__init__()

        self.features = torch.nn.Sequential(*list(base_model.children())[:-2])
        self.avgpool = torch.nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        return x.reshape(-1)


model = FeatureExtractor(base_model)
model = model.to(conf.device)
model.eval()

def convert_image_to_rgb(image):
    if image.mode == 'RGBA': return image.convert('RGB')
    return image

def toB64(path):
    if isinstance(path, str):
        with open(path, 'rb') as f:
            image = f.read()
        return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')
    elif isinstance(path, bytes):
        return 'data:image/png;base64,' + base64.b64encode(path).decode('utf-8')
    elif isinstance(path, Image.Image):
        buffer = BytesIO()
        path.save(buffer, format="PNG")
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        return 'data:image/png;base64,' + base64.b64encode(image_bytes).decode('utf-8')

    return None

transform = Compose([
    convert_image_to_rgb,
    Resize((224, 224)),
    ToTensor(),
    Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extractFeatures(image):
    image_tensor = transform(image).unsqueeze(0)
    image_tensor = image_tensor.to(conf.device)
    with torch.no_grad():
        features = model(image_tensor)

    feature_length = features.shape[0]
    if feature_length != 2048:
        if feature_length > 2048: features = features[:2048]
        else:
            padded = torch.zeros(2048, device=conf.device)
            padded[:feature_length] = features
            features = padded

    features = torch.nn.functional.normalize(features, p=2, dim=0)

    np_features = features.cpu().numpy()
    if np_features is None or np_features.size == 0 or not np.isfinite(np_features).all():
        raise ValueError("Extracted vector is empty or contains invalid values")

    return np_features

def saveVectorBy(assetId, img):
    try:
        if img is None:
            lg.warn(f'assetId[{assetId}] image is None')
            return None

        try:
            features = extractFeatures(img)

            if not isinstance(features, np.ndarray) or features.size != 2048:
                raise ValueError(f"assetId[{assetId}] vector incorrect: size={features.size if isinstance(features, np.ndarray) else 'unknown'}")

            saved = db.vecs.save(assetId, features)
        except ValueError as ve:
            return f"assetId[{assetId}] vector processing error: {str(ve)}"

        if saved: return True

        return False
    except Exception as e:
        raise RuntimeError( f"Error processing asset {assetId}: {str(e)}" )


def fixPath(path: Optional[str]):
    if path and not path.startswith(envs.immichPath):
        path = os.path.join(envs.immichPath, path)
    return path

def getImg(path) -> Optional[Image.Image]:
    path = fixPath(path)
    try:
        if os.path.exists(path):
            size = os.path.getsize(path)
            # lg.info(f"[getImgLocal] image[{os.path.basename(path)}] size[{size / 1024 / 1024:.2f} MB]")
            image = Image.open(path)
            image.load()
            return image
        else:
            lg.error(f"File not found: {path}")
    except Exception as e:
        lg.error(f"Error opening image from local path: {str(e)}")

    return None

def getImgB64(path) -> Optional[str]:
    img = getImg(path)
    if img: return toB64(img)

    return toB64(path) if os.path.exists(path) else None


def processAsset(asset: models.Asset, photoQ) -> Tuple[models.Asset, bool, Optional[str]]:
    try:
        img = getImg(asset.getImagePath(photoQ))
        if not img:
            return asset, False, f"Unable to get photo: assetId[{asset.id}], photoQ[{photoQ}]"

        result = saveVectorBy(asset.id, img)
        if result is True:
            return asset, True, None
        elif result is False or result is None:
            return asset, None, None
        else:
            return asset, False, str(result)
    except Exception as e:
        return asset, False, f"Processing failed: {asset.id} - {str(e)}"


def toVectors(assets: List[models.Asset], photoQ, onUpdate: models.IFnProg = None) -> models.ProcessInfo:
    tS = time.time()
    pi = models.ProcessInfo(total=len(assets), done=0, skip=0, error=0)
    inPct = 15

    numWorkers = min(multiprocessing.cpu_count(), 8)
    commitBatch = 100

    lock = threading.Lock()
    processedCnt = 0
    updAssets = []
    lastUpdateTime = 0

    try:
        if onUpdate:
            onUpdate(inPct, f"Preparing to process count[{pi.total}], quality: {photoQ}, workers: {numWorkers}")

        with ThreadPoolExecutor(max_workers=numWorkers) as executor:
            futures = {executor.submit(processAsset, asset, photoQ): asset for asset in assets}

            for future in as_completed(futures):
                asset = futures[future]
                try:
                    asset, result, error = future.result()

                    with lock:
                        if error:
                            lg.error(error)
                            pi.error += 1
                        elif result is True:
                            pi.done += 1
                            updAssets.append(asset)
                        elif result is None:
                            pi.skip += 1
                        else:
                            pi.error += 1

                        processedCnt += 1

                        if len(updAssets) >= commitBatch:
                            assetsBatch = updAssets[:]
                            updAssets = []
                            with db.pics.mkConn() as conn:
                                cur = conn.cursor()
                                for a in assetsBatch:
                                    db.pics.updVecBy(a, cur=cur)
                                conn.commit()

                        currentTime = time.time()
                        tElapsed = currentTime - tS

                        needUpdate = (processedCnt % 10 == 0 or processedCnt == pi.total or
                                    processedCnt < 10 or (currentTime - lastUpdateTime) > 1)

                        if onUpdate and needUpdate:
                            lastUpdateTime = currentTime

                            if processedCnt >= 5:
                                avgTimePerItem = tElapsed / processedCnt
                                remainCnt = pi.total - processedCnt
                                remainTimeSec = avgTimePerItem * remainCnt * 1.1

                                if remainTimeSec < 60:
                                    remainStr = f"{int(remainTimeSec)} seconds"
                                elif remainTimeSec < 3600:
                                    mins = remainTimeSec / 60
                                    remainStr = f"{mins:.1f} minutes" if mins >= 1 else "< 1 minute"
                                else:
                                    hours = int(remainTimeSec / 3600)
                                    mins = int((remainTimeSec % 3600) / 60)
                                    remainStr = f"{hours}h {mins}m"
                            else:
                                remainStr = "Calculating..."

                            percent = inPct + int(processedCnt / pi.total * (100 - inPct))
                            itemsPerSec = processedCnt / tElapsed if tElapsed > 0 else 0
                            speedStr = f" ({itemsPerSec:.1f} items/sec)" if itemsPerSec > 0 else ""

                            msg = f"Processing {processedCnt}/{pi.total}, done[{pi.done}] skip[{pi.skip}] error[{pi.error}]"
                            msg += f" ( Estimated remaining: {remainStr}{speedStr} )"
                            onUpdate(percent, msg)

                except Exception as e:
                    with lock:
                        lg.error(f"Future execution failed for {asset.id}: {str(e)}")
                        pi.error += 1
                        processedCnt += 1

        if updAssets:
            with db.pics.mkConn() as conn:
                cur = conn.cursor()
                for asset in updAssets:
                    db.pics.updVecBy(asset, cur=cur)
                conn.commit()

        if onUpdate:
            onUpdate(100, f"Processing completed! Completed: {pi.done}, Skipped: {pi.skip}, Errors: {pi.error}")

        return pi

    except Exception as e:
        raise mkErr("Failed to generate vectors for assets", e)
