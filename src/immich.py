from os import wait
from typing import List, Tuple

import requests
import re

from conf import ks
from util import log, err
from mod import models

lg = log.get(__name__)

def getGithubRaw(url):
    url = url.replace('github.com', 'raw.githubusercontent.com')
    url = url.replace('/blob/', '/')

    try:
        # lg.info( f"[code] checking.. url[{url}]" )
        rep = requests.get(url)
        rep.raise_for_status()
        return rep.text
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"request url[{url}] failed: {e}")

def checkCodeBy(src, target_code):
    if not src: ValueError( f"src[{src}]" )

    clean_src = re.sub(r'\s+', '', src)
    clean_code = re.sub(r'\s+', '', target_code)

    ok = clean_code in clean_src

    if not ok: lg.error( f"[checkCode] expect `{clean_code}` not in target: {clean_src}" )

    return ok


url_delete = "https://github.com/immich-app/immich/blob/main/server/src/services/asset.service.ts"
code_deleteAll = """
    await this.assetRepository.updateAll(ids, {
      deletedAt: new Date(),
      status: force ? AssetStatus.DELETED : AssetStatus.TRASHED,
    });
"""

url_restore = "https://github.com/immich-app/immich/blob/main/server/src/repositories/trash.repository.ts"
code_Restore = """
  async restore(userId: string): Promise<number> {
    const { numUpdatedRows } = await this.db
      .updateTable('assets')
      .where('ownerId', '=', userId)
      .where('status', '=', AssetStatus.TRASHED)
      .set({ status: AssetStatus.ACTIVE, deletedAt: null })
      .executeTakeFirst();
"""


def checkBy(url, code):
    src = getGithubRaw(url)
    if not src: raise RuntimeError(f"cannot fetch content from url[{url}]")

    ok = checkCodeBy(src, code)

    return ok

def checkLogicDelete():
    return checkBy(url_delete, code_deleteAll)

def checkLogicRestore():
    return checkBy(url_restore, code_Restore)




from db import psql
#------------------------------------------------------------------------
# delete
#
# This function moves multiple assets to trash by updating their status to 'trashed' and setting deletedAt timestamp
# Note: This implementation follows Immich's API flow which may change in future versions
# follow delete flow
# https://github.com/immich-app/immich/blob/main/server/src/services/asset.service.ts#L231
#------------------------------------------------------------------------
def trashBy(assetIds: List[str]):
    try:
        if not assetIds or len(assetIds) <= 0: raise RuntimeError(f"can't delete assetIds empty {assetIds}")

        with psql.mkConn() as cnn:
            with cnn.cursor() as cursor:
                sql = """
                Update assets
                Set "deletedAt" = Now(), status = %s
                Where id = ANY(%s)
                """
                cursor.execute(sql, (ks.db.status.trashed, assetIds))
                affectedRows = cursor.rowcount
                cnn.commit()

                return affectedRows
    except Exception as e:
        raise err.mkErr(f"Failed to delete assets: {str(e)}", e)

#------------------------------------------------------------------------
# delete by assets list
#------------------------------------------------------------------------
def trashByAssets(assets: List[models.Asset]):
    if not assets: return 0
    assetIds = [ass.id for ass in assets]
    return trashBy(assetIds)

#------------------------------------------------------------------------
# This function restores multiple assets from trash by updating their status back to 'active' and clearing deletedAt
# Note: This implementation follows Immich's API flow which may change in future versions
# restore flow
# https://github.com/immich-app/immich/blob/main/server/src/repositories/trash.repository.ts#L15
#------------------------------------------------------------------------
def restoreBy(assetIds: List[str]):
    try:
        if not assetIds or len(assetIds) <= 0: raise RuntimeError(f"can't restore assetIds empty {assetIds}")

        with psql.mkConn() as cnn:
            with cnn.cursor() as cursor:
                sql = """
                Update assets
                Set "deletedAt" = Null, status = %s
                Where id = ANY(%s) And status = %s
                """
                cursor.execute(sql, (ks.db.status.active, assetIds, ks.db.status.trashed))
                affectedRows = cursor.rowcount
                cnn.commit()

                return affectedRows
    except Exception as e:
        raise err.mkErr(f"Failed to restore assets: {str(e)}", e)










#------------------------------------------------------
# Album Repository Verification
#------------------------------------------------------
urlAlbumRepo = "https://github.com/immich-app/immich/blob/main/server/src/repositories/album.repository.ts"

codeAlbumAssAdd = """
async addAssets(db: Kysely<DB>, albumId: string, assetIds: string[]): Promise<void> {
  if (assetIds.length === 0) {
    return;
  }

  await db
    .insertInto('albums_assets_assets')
    .values(assetIds.map((assetId) => ({ albumsId: albumId, assetsId: assetId })))
    .execute();
}
"""

codeAlbumAssDel = """
async removeAssetIds(albumId: string, assetIds: string[]): Promise<void> {
  if (assetIds.length === 0) {
    return;
  }

  await this.db
    .deleteFrom('albums_assets_assets')
    .where('albums_assets_assets.albumsId', '=', albumId)
    .where('albums_assets_assets.assetsId', 'in', assetIds)
    .execute();
}
"""


def checkAlbAssAdd():
    return checkBy(urlAlbumRepo, codeAlbumAssAdd)

def checkAlbumAssDel():
    return checkBy(urlAlbumRepo, codeAlbumAssDel)


#------------------------------------------------------
# Asset Service/Repository Verification
#------------------------------------------------------
urlAssetService = "https://github.com/immich-app/immich/blob/main/server/src/services/asset.service.ts"
urlAssetRepo = "https://github.com/immich-app/immich/blob/main/server/src/repositories/asset.repository.ts"

codeAssetUpdateAll = """
  async updateAll(auth: AuthDto, dto: AssetBulkUpdateDto): Promise<void> {
    const { ids, description, dateTimeOriginal, latitude, longitude, ...options } = dto;
    await this.requireAccess({ auth, permission: Permission.ASSET_UPDATE, ids });

    if (
      description !== undefined ||
      dateTimeOriginal !== undefined ||
      latitude !== undefined ||
      longitude !== undefined
    ) {
      await this.assetRepository.updateAllExif(ids, { description, dateTimeOriginal, latitude, longitude });
      await this.jobRepository.queueAll(
        ids.map((id) => ({
          name: JobName.SIDECAR_WRITE,
          data: { id, description, dateTimeOriginal, latitude, longitude },
        })),
      );
    }

    if (
      options.visibility !== undefined ||
      options.isFavorite !== undefined ||
      options.duplicateId !== undefined ||
      options.rating !== undefined
    ) {
      await this.assetRepository.updateAll(ids, options);

      if (options.visibility === AssetVisibility.LOCKED) {
        await this.albumRepository.removeAssetsFromAll(ids);
      }
    }
  }
"""

codeAssetRepoUpdate = """
  async updateAll(ids: string[], options: Updateable<Assets>): Promise<void> {
    if (ids.length === 0) {
      return;
    }

    await this.db
      .updateTable('assets')
      .set(options)
      .where('id', '=', anyUuid(ids))
      .execute();
  }
"""


def checkAssetUpdateLogic():
    return checkBy(urlAssetService, codeAssetUpdateAll)


def checkAssetRepositoryUpdate():
    return checkBy(urlAssetRepo, codeAssetRepoUpdate)

