import os
import time
import torch

from typing import List

import numpy as np
from torchvision.models import resnet152, ResNet152_Weights
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

os.environ['KMP_DUPLICATE_LIB_OK'] = "TRUE"

# noinspection PyUnresolvedReferences
import api, db, conf
from util import log, models

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

def getImageFromLocal(assetId, photoQ):
    file_path = db.pics.getAssetImagePathBy(assetId, photoQ)
    lg.info(f"[getImgLocal] id[{assetId}], photoQ[{photoQ}] path[{file_path}]")

    if file_path:
        full_path = os.path.join(conf.envs.immichPath, file_path.lstrip('/'))

        try:
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                lg.info(f"[getImgLocal] image[{os.path.basename(full_path)}] size[{size / 1024 / 1024:.2f} MB]")
                image = Image.open(full_path)
                image.load()
                return image
            else:
                lg.error(f"File not found: {full_path}")
        except Exception as e:
            lg.error(f"Error opening image from local path: {str(e)}")

    return None

def saveVectorBy(assetId, img):
    try:
        if img is None:
            lg.info(f'assetId[{assetId}] image is None')
            return 'skipped'

        try:
            features = extractFeatures(img)

            if not isinstance(features, np.ndarray) or features.size != 2048:
                raise ValueError(f"Photo {assetId} vector format is incorrect: size={features.size if isinstance(features, np.ndarray) else 'unknown'}")

            vector_saved = db.vecs.save(assetId, features)
        except ValueError as ve:
            return f"Photo {assetId} vector processing error: {str(ve)}"

        if vector_saved: return 'processed'

        return 'skipped'
    except Exception as e:
        error_msg = f"Error processing asset {assetId}: {str(e)}"
        lg.error(error_msg)
        return error_msg

def processPhotoToVectors(assets: List[models.Asset], photoQ, onUpdate=None):
    cntAll = len(assets)

    cntOk = 0
    cntSkip = 0
    cntErr = 0
    tS = time.time()

    if onUpdate:
        onUpdate([0, "0%", f"Starting to process {cntAll} photos, photo quality: {photoQ}"])

    for idx, asset in enumerate(assets):
        assetId = asset.id

        # img = api.getImage(apiKey, assetId, photoQ)
        img = getImageFromLocal(assetId, photoQ)

        if not img:
            lg.error(f"Cannot get photo: assetId[{assetId}], photoQ[{photoQ}]")
            cntErr += 1
            continue

        result = saveVectorBy(assetId, img)

        if isinstance(result, tuple) and result[0] == 'error':
            error_msg = result[1]
            lg.error(error_msg)
            cntErr += 1
        elif result == 'processed':
            cntOk += 1
        elif result == 'skipped':
            cntSkip += 1

        if idx > 0:
            tElapsed = time.time() - tS
            tPerItem = tElapsed / (idx + 1)
            remainCnt = cntAll - (idx + 1)
            remainTime = tPerItem * remainCnt
            remainMins = int(remainTime / 60)
        else:
            remainMins = "calculating"

        if onUpdate and (idx % 10 == 0 or idx == cntAll - 1):
            percent = int((idx + 1) / cntAll * 100)
            onUpdate([percent, f"{percent}%", f"Processing photo {idx + 1}/{cntAll} - (Processed: {cntOk}, Skipped: {cntSkip}, Errors: {cntErr}). Estimated time remaining: {remainMins} minutes"])

    if onUpdate:
        onUpdate([100, "100%", f"Processing complete! Processed: {cntOk}, Skipped: {cntSkip}, Errors: {cntErr}"])

    return {
        "processed": cntOk,
        "skipped": cntSkip,
        "errors": cntErr,
        "total": cntAll
    }
