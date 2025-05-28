import requests
import re

from util import log

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
