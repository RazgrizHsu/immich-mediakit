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

def getOptimalBatchSize():
    device_type = conf.device.type

    if device_type == 'cpu':
        return 1
    elif device_type == 'cuda': # NVIDIA GPU (Linux/Windows)
        try:
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            if gpu_memory > 12 * 1024**3: return 16    # 12GB+ (RTX 3090, 4090)
            elif gpu_memory > 8 * 1024**3: return 12   # 8-12GB (RTX 3080, 4070)
            elif gpu_memory > 6 * 1024**3: return 8    # 6-8GB (RTX 3060 Ti)
            elif gpu_memory > 4 * 1024**3: return 6    # 4-6GB (RTX 3060)
            elif gpu_memory > 2 * 1024**3: return 4    # 2-4GB
            else: return 2  # <2GB
        except:
            return 8
    elif device_type == 'mps': # Apple Silicon GPU (macOS)
        try:
            import platform
            if 'arm64' in platform.machine().lower():
                import psutil
                total_memory = psutil.virtual_memory().total
                if total_memory > 32 * 1024**3: return 64    # 32GB+ (M2 Ultra)
                elif total_memory > 16 * 1024**3: return 32   # 16-32GB (M2 Pro/Max)
                elif total_memory > 8 * 1024**3: return 16    # 8-16GB (M2)
                else: return 8  # 8GB (M1)
            return 8
        except:
            return 8
    else:
        return 8

def convert_image_to_rgb(image):
    if image.mode == 'RGBA': return image.convert('RGB')
    return image


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

def extractFeaturesBatch(images: List[Image.Image]) -> List[np.ndarray]:
    if not images: return []

    device_type = conf.device.type

    try:
        image_tensors = []
        for img in images:
            tensor = transform(img)
            image_tensors.append(tensor)

        batch_tensor = torch.stack(image_tensors)

        if device_type == 'cuda':
            batch_tensor = batch_tensor.to(conf.device, non_blocking=True)
        elif device_type == 'mps':
            batch_tensor = batch_tensor.to(conf.device, non_blocking=False)
        else:
            batch_tensor = batch_tensor.to(conf.device)

        with torch.no_grad(): features_batch = model(batch_tensor)

        # 修正 MPS 批次輸出格式問題
        if device_type == 'mps' and len(features_batch.shape) == 1:
            # MPS 可能輸出扁平向量，需要重塑為批次格式
            batch_size = batch_tensor.shape[0]
            expected_feature_size = features_batch.shape[0] // batch_size
            features_batch = features_batch.view(batch_size, expected_feature_size)

        # 批次處理特徵向量維度調整（在 GPU 上完成）
        batch_size = features_batch.shape[0]
        feature_dim = features_batch.shape[1]

        if feature_dim != 2048:
            if feature_dim > 2048:
                features_batch = features_batch[:, :2048]
            else:
                padded_batch = torch.zeros(batch_size, 2048, device=conf.device)
                padded_batch[:, :feature_dim] = features_batch
                features_batch = padded_batch

        features_batch_normalized = torch.nn.functional.normalize(features_batch, p=2, dim=1)

        if device_type == 'mps':
            batch_numpy = features_batch_normalized.detach().cpu().numpy()
        else:
            batch_numpy = features_batch_normalized.cpu().numpy()

        results = []
        for i in range(batch_size):
            vec = batch_numpy[i]

            if vec is None or vec.size == 0 or not np.isfinite(vec).all():
                raise ValueError(f"Extracted vector {i} is empty or contains invalid values")

            if not isinstance(vec, np.ndarray) or vec.size != 2048:
                raise ValueError(f"vector {i} incorrect: size[{vec.size if isinstance(vec, np.ndarray) else 'unknown'}]")

            results.append(vec)

        return results

    except Exception as e:
        lg.warning(f"Batch processing failed on {device_type} with {len(images)} images, falling back to single processing. Error: {type(e).__name__}: {str(e)}")
        results = []
        for img in images:
            try:
                vec = extractFeatures(img)
                results.append(vec)
            except Exception as single_e:
                raise ValueError(f"Single image processing also failed: {str(single_e)}")
        return results



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

def fixPath(path: Optional[str]) -> str:
    if path and not path.startswith(envs.immichPath):
        path = os.path.join(envs.immichPath, path)

    return path if path else ""

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
        db.vecs.save(asset.autoId, vec)

        return asset, None

    except Exception as e:
        return asset, f"save vector failed: {asset.id} - {str(e)}"

def loadImagesParallel(assets: List[models.Asset], photoQ, maxWorkers: int = 10) -> Tuple[List[Image.Image], List[models.Asset], List[Tuple[models.Asset, Optional[str]]]]:
    imgs = []
    rstOKs = []
    rstNos = []

    def doLoadImg(asset):
        try:
            path = asset.getImagePath(photoQ)
            img = getImg(path)
            if img:
                return asset, img, None
            else:
                return asset, None, f"Failed to load image: {path}"
        except Exception as e:
            return asset, None, f"Error loading image {asset.id}: {str(e)}"

    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        futureImg = {executor.submit(doLoadImg, asset): asset for asset in assets}

        for future in as_completed(futureImg):
            asset, img, error = future.result()
            if img:
                imgs.append(img)
                rstOKs.append(asset)
            else:
                rstNos.append((asset, error))

    return imgs, rstOKs, rstNos

def saveVectorBatch(assets: List[models.Asset], photoQ) -> List[Tuple[models.Asset, Optional[str]]]:
    imgs, rstOKs, rstNos = loadImagesParallel(assets, photoQ)

    results = rstNos
    if not imgs: return results

    try:
        vecs = extractFeaturesBatch(imgs)

        for asset, vec in zip(rstOKs, vecs):
            try:
                db.vecs.save(asset.autoId, vec)
                results.append((asset, None))
            except Exception as e:
                results.append((asset, f"Save vector failed {asset.id}: {str(e)}"))

    except Exception as e:

        # fallback
        for idx, asset in enumerate(rstOKs):
            try:
                if idx < len(imgs):
                    vec = extractFeatures(imgs[idx])
                    db.vecs.save(asset.autoId, vec)
                    results.append((asset, None))
                else:
                    results.append((asset, f"No corresponding image for asset {asset.id}"))
            except Exception as fallback_e:
                results.append((asset, f"Fallback failed {asset.id}: {str(fallback_e)}"))

    return results


def processVectors(assets: List[models.Asset], photoQ, onUpdate: models.IFnProg, isCancelled: models.IFnCancel) -> models.ProcessInfo:
    tS = time.time()
    pi = models.ProcessInfo(all=len(assets), done=0, skip=0, erro=0)
    inPct = 15

    batchSize = getOptimalBatchSize()
    commitBatch = 100
    device_type = conf.device.type

    if device_type in ['cuda', 'mps']:
        numWorkers = 1
    else:
        numWorkers = min(multiprocessing.cpu_count() // 2, 4)

    lock = threading.Lock()
    cntDone = 0
    updAssets = []
    lastUpdateTime = 0

    try:
        if onUpdate:
            if device_type == 'cuda':
                try:
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    deviceStr = f"NVIDIA {gpu_name} ({gpu_memory:.1f}GB, batch={batchSize})"
                except:
                    deviceStr = f"CUDA GPU (batch={batchSize})"
            elif device_type == 'mps':
                try:
                    import platform
                    system_info = platform.processor() or "Apple Silicon"
                    deviceStr = f"Apple {system_info} GPU (MPS, batch={batchSize})"
                except:
                    deviceStr = f"Apple GPU (MPS, batch={batchSize})"
            else:
                cpu_count = multiprocessing.cpu_count()
                deviceStr = f"CPU ({cpu_count} cores, workers={numWorkers})"

            onUpdate(inPct, f"Processing [{pi.all}] images on {deviceStr}")

        batches = []
        for i in range(0, len(assets), batchSize):
            batch = assets[i:i + batchSize]
            batches.append(batch)

        if device_type in ['cuda', 'mps'] and batchSize > 1:
            lg.info(f"[imgs] Using {device_type.upper()} batch processing: {len(batches)} batches of size {batchSize}")

            for batchIdx, batch in enumerate(batches):
                if isCancelled and isCancelled():
                    lg.info("[imgs] Processing cancelled by user")
                    pi.erro = len(assets) - cntDone
                    break

                try:
                    results = saveVectorBatch(batch, photoQ)

                    with lock:
                        for asset, error in results:
                            if error:
                                lg.error(error)
                                pi.erro += 1
                            else:
                                pi.done += 1
                                updAssets.append(asset)
                            cntDone += 1

                        # 批次提交資料庫更新
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
                        needUpdate = (batchIdx % 5 == 0 or batchIdx == len(batches) - 1 or (currentTime - lastUpdateTime) > 1)

                        if onUpdate and needUpdate:
                            lastUpdateTime = currentTime

                            if cntDone >= 5:
                                avgTimePerItem = tElapsed / cntDone
                                remainCnt = pi.all - cntDone
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

                            percent = inPct + int(cntDone / pi.all * (100 - inPct))
                            itemsPerSec = cntDone / tElapsed if tElapsed > 0 else 0
                            speedStr = f" {itemsPerSec:.1f} items/sec" if itemsPerSec > 0 else ""

                            msg = f"{device_type.upper()} Batch: {cntDone}/{pi.all} ok[{pi.done}]"
                            if pi.skip: msg += f" skip[{pi.skip}]"
                            if pi.erro: msg += f" error[{pi.erro}]"
                            msg += f" ( remaining: {remainStr}{speedStr} )"
                            onUpdate(percent, msg)

                except Exception as e:
                    lg.error(f"Batch processing failed: {str(e)}")
                    with lock:
                        pi.erro += len(batch)
                        cntDone += len(batch)

        else:
            lg.info(f"[imgs] Using CPU threading: {numWorkers} workers")

            with ThreadPoolExecutor(max_workers=numWorkers) as executor:
                futures = {executor.submit(saveVectorBy, asset, photoQ): asset for asset in assets}

                for future in as_completed(futures):
                    if isCancelled and isCancelled():
                        lg.info("[imgs] Processing cancelled by user")
                        executor.shutdown(wait=False, cancel_futures=True)
                        pi.erro = len(assets) - cntDone
                        break

                    asset = futures[future]
                    try:
                        asset, error = future.result()

                        with lock:
                            if error:
                                lg.error(error)
                                pi.erro += 1
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
                            needUpdate = (cntDone % 10 == 0 or cntDone == pi.all or
                                          cntDone < 10 or (currentTime - lastUpdateTime) > 1)

                            if onUpdate and needUpdate:
                                if isCancelled and isCancelled():
                                    lg.info("[imgs] Processing cancelled during update")
                                    break

                                lastUpdateTime = currentTime

                                if cntDone >= 5:
                                    avgTimePerItem = tElapsed / cntDone
                                    remainCnt = pi.all - cntDone
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

                                percent = inPct + int(cntDone / pi.all * (100 - inPct))
                                itemsPerSec = cntDone / tElapsed if tElapsed > 0 else 0
                                speedStr = f" {itemsPerSec:.1f} items/sec" if itemsPerSec > 0 else ""

                                msg = f"CPU Threading: {cntDone}/{pi.all} ok[{pi.done}]"
                                if pi.skip: msg += f" skip[{pi.skip}]"
                                if pi.erro: msg += f" error[{pi.erro}]"
                                msg += f" ( remaining: {remainStr}{speedStr} )"
                                onUpdate(percent, msg)

                    except Exception as e:
                        with lock:
                            lg.error(f"Future execution failed for {asset.id}: {str(e)}")
                            pi.erro += 1
                            cntDone += 1

        # 最後提交剩餘的更新
        if updAssets:
            with db.pics.mkConn() as conn:
                cur = conn.cursor()
                for asset in updAssets:
                    db.pics.setVectoredBy(asset, cur=cur)
                conn.commit()

        if isCancelled and isCancelled():
            if onUpdate:
                onUpdate(0, f"Processing cancelled! Completed: {pi.done}, Errors: {pi.erro}")
            return pi

        if onUpdate:
            finalElapsed = time.time() - tS
            finalSpeed = pi.done / finalElapsed if finalElapsed > 0 else 0
            onUpdate(100, f"Completed! done[{pi.done}] skip[{pi.skip}] error[{pi.erro}] ({finalSpeed:.1f} items/sec)")

        return pi

    except Exception as e:
        raise mkErr("Failed to generate vectors for assets", e)
