from typing import List, Tuple

import requests
import re

from conf import ks
from util import log, err

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
