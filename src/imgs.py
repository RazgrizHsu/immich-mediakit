import os
import time
import torch

from typing import List, Optional

import numpy as np
from torchvision.models import resnet152, ResNet152_Weights
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

os.environ['KMP_DUPLICATE_LIB_OK'] = "TRUE"

# noinspection PyUnresolvedReferences
import api, db, conf
from util import log, models
from util.task import IFnProg


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
            return f"Photo {assetId} vector processing error: {str(ve)}"

        if saved: return True

        return False
    except Exception as e:
        raise f"Error processing asset {assetId}: {str(e)}"

def getImage(path) -> Optional[Image.Image]:
    if path:
        path = os.path.join(conf.envs.immichPath, path.lstrip('/'))

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

def getImageFromLocal(assetId, photoQ):
    path = db.pics.getAssetImagePathBy(assetId, photoQ)
    lg.info(f"[getImgLocal] id[{assetId}], photoQ[{photoQ}] path[{path}]")
    return getImage(path)


def testDirectAccess():
    import db.pics as pics
    assets = pics.getAll(1)
    asset = assets[0] if assets else None

    if not asset: return "No Assets"

    path = asset.getImagePath(conf.Ks.db.preview)


    if os.path.exists(path):
        return "OK! path exists!"
    else:
        lg.warn( f"[imgs] image path not exist: {path}" )

    return f"access failed"

def processPhotoToVectors(assets: List[models.Asset], photoQ, onUpdate:IFnProg=None) -> models.ProcessInfo:
    tS = time.time()
    pi = models.ProcessInfo(total=len(assets), done=0, skip=0, error=0)

    # 初始進度為15%
    inPct = 15

    if onUpdate:
        onUpdate(inPct, f"{inPct}%", f"準備處理 {pi.total} 張照片, 品質: {photoQ}")

    for idx, asset in enumerate(assets):
        assetId = asset.id

        # img = api.getImage(apiKey, assetId, photoQ)
        img = getImageFromLocal(assetId, photoQ)

        if not img:
            lg.error(f"無法取得照片: assetId[{assetId}], photoQ[{photoQ}]")
            pi.error += 1
            continue

        try:
            result = saveVectorBy(assetId, img)

            if result is True:
                pi.done += 1
            elif result is False or result is None:
                pi.skip += 1
        except Exception as e:
            lg.error(f"處理失敗: {assetId} - {str(e)}")
            pi.error += 1

        if idx > 0:
            tElapsed = time.time() - tS
            tPerItem = tElapsed / (idx + 1)
            remainCnt = pi.total - (idx + 1)
            remainTime = tPerItem * remainCnt
            remainMins = int(remainTime / 60)
        else:
            remainMins = "計算中"

        if onUpdate and (idx % 10 == 0 or idx == pi.total - 1):
            # 將剩餘的85%進度分配給實際處理過程
            percent = inPct + int((idx + 1) / pi.total * (100 - inPct))
            onUpdate(percent, f"{percent}%", f"處理照片 {idx + 1}/{pi.total} - (完成: {pi.done}, 跳過: {pi.skip}, 錯誤: {pi.error}). 預估剩餘時間: {remainMins} 分鐘")

    if onUpdate:
        onUpdate(100, "100%", f"處理完成! 完成: {pi.done}, 跳過: {pi.skip}, 錯誤: {pi.error}")

    return pi
