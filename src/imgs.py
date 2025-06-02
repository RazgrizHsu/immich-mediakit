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

def extractFeatures(image) -> np.ndarray:
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

    vec = features.cpu().numpy()
    if vec is None or vec.size == 0 or not np.isfinite(vec).all():
        raise ValueError("Extracted vector is empty or contains invalid values")

    if not isinstance(vec, np.ndarray) or vec.size != 2048:
        raise ValueError(f"vector incorrect: size[{vec.size if isinstance(vec, np.ndarray) else 'unknown'}]")

    return vec


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


def saveVectorBy(asset: models.Asset, photoQ) -> Tuple[models.Asset, Optional[str]]:
    try:
        path = asset.getImagePath(photoQ)
        img = getImg(path)

        vec = extractFeatures(img)
        db.vecs.save(asset.id, vec)

        return asset, None

    except Exception as e:
        return asset, f"save vector failed: {asset.id} - {str(e)}"


def processVectors(assets: List[models.Asset], photoQ, onUpdate: models.IFnProg = None) -> models.ProcessInfo:
    tS = time.time()
    pi = models.ProcessInfo(total=len(assets), done=0, skip=0, error=0)
    inPct = 15

    numWorkers = min(multiprocessing.cpu_count(), 8)
    commitBatch = 100

    lock = threading.Lock()
    cntDone = 0
    updAssets = []
    lastUpdateTime = 0

    try:
        if onUpdate:
            onUpdate(inPct, f"Preparing to process count[{pi.total}], quality: {photoQ}, workers: {numWorkers}")

        with ThreadPoolExecutor(max_workers=numWorkers) as executor:
            futures = {executor.submit(saveVectorBy, asset, photoQ): asset for asset in assets}

            for future in as_completed(futures):
                asset = futures[future]
                try:
                    asset, error = future.result()

                    with lock:
                        if error:
                            lg.error(error)
                            pi.error += 1
                        else:
                            pi.done += 1
                            updAssets.append(asset)

                        cntDone += 1

                        if len(updAssets) >= commitBatch:
                            assetsBatch = updAssets[:]
                            updAssets = []
                            with db.pics.mkConn() as conn:
                                cur = conn.cursor()
                                for a in assetsBatch:
                                    db.pics.setVectoredBy(a, cur=cur)
                                conn.commit()

                        currentTime = time.time()
                        tElapsed = currentTime - tS

                        needUpdate = (cntDone % 10 == 0 or cntDone == pi.total or
                                      cntDone < 10 or (currentTime - lastUpdateTime) > 1)

                        if onUpdate and needUpdate:
                            lastUpdateTime = currentTime

                            if cntDone >= 5:
                                avgTimePerItem = tElapsed / cntDone
                                remainCnt = pi.total - cntDone
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

                            percent = inPct + int(cntDone / pi.total * (100 - inPct))
                            itemsPerSec = cntDone / tElapsed if tElapsed > 0 else 0
                            speedStr = f" ({itemsPerSec:.1f} items/sec)" if itemsPerSec > 0 else ""

                            msg = f"Processing {cntDone}/{pi.total}, done[{pi.done}] skip[{pi.skip}] error[{pi.error}]"
                            msg += f" ( Estimated remaining: {remainStr}{speedStr} )"
                            onUpdate(percent, msg)

                except Exception as e:
                    with lock:
                        lg.error(f"Future execution failed for {asset.id}: {str(e)}")
                        pi.error += 1
                        cntDone += 1

        if updAssets:
            with db.pics.mkConn() as conn:
                cur = conn.cursor()
                for asset in updAssets:
                    db.pics.setVectoredBy(asset, cur=cur)
                conn.commit()

        if onUpdate:
            onUpdate(100, f"Processing completed! Completed: {pi.done}, Skipped: {pi.skip}, Errors: {pi.error}")

        return pi

    except Exception as e:
        raise mkErr("Failed to generate vectors for assets", e)
