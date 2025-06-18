import os
from dataclasses import dataclass
from typing import List

from conf import envs
from util import log

import db
import immich

lg = log.get(__name__)

@dataclass
class ChkInfo:
    ok: bool
    msg: str
    details: str = ''

@dataclass
class SysStatus:
    psql: ChkInfo
    immichPath: ChkInfo
    qdrant: ChkInfo
    immichLogic: ChkInfo

    @property
    def allOk(self) -> bool:
        return all(check.ok for check in [self.psql, self.immichPath, self.qdrant, self.immichLogic])

def psql() -> ChkInfo:
    try:
        if not all([envs.psqlHost, envs.psqlPort, envs.psqlDb, envs.psqlUser]):
            return ChkInfo(False, 'PostgreSQL settings incomplete', 'Missing required connection parameters')

        if not db.psql.init():
            return ChkInfo(False, 'Cannot connect to PostgreSQL', 'Connection test failed')

        return ChkInfo(True, 'IMMICH_PATH accessible', f'Path: {envs.immichPath}')
    except Exception as e:
        return ChkInfo(False, 'PostgreSQL check failed', str(e))

def immichPath() -> ChkInfo:
    try:
        if not envs.immichPath: return ChkInfo(False, 'IMMICH_PATH not configured')

        if not os.path.exists(envs.immichPath): return ChkInfo(False, 'IMMICH_PATH does not exist', f'Path: {envs.immichPath}')

        if not os.path.isdir(envs.immichPath): return ChkInfo(False, 'IMMICH_PATH is not a directory', f'Path: {envs.immichPath}')

        if not os.access(envs.immichPath, os.R_OK): return ChkInfo(False, 'IMMICH_PATH is not readable', f'Path: {envs.immichPath}')

        rst = db.psql.testAssetsPath()
        if rst == "No Assets":
            return ChkInfo(True, 'No assets found in database', 'Database connected but no assets available')
        elif not rst.startswith("OK"):
            return ChkInfo(False, 'Asset path test failed', rst)

        return ChkInfo(True, 'IMMICH_PATH accessible', f'Path: {envs.immichPath}')

    except Exception as e:
        return ChkInfo(False, 'IMMICH_PATH check failed', str(e))

def qdrant() -> ChkInfo:
    try:
        if not envs.qdrantUrl: return ChkInfo(False, 'Qdrant URL not configured')

        db.vecs.init()

        return ChkInfo(True, 'Qdrant connection OK', f'URL: {envs.qdrantUrl}')

    except Exception as e:
        return ChkInfo(False, 'Qdrant check failed', str(e))

def immichLogic() -> ChkInfo:
    try:
        chkDel = immich.checkLogicDelete()
        chkRst = immich.checkLogicRestore()

        if chkDel and chkRst:
            return ChkInfo(True, 'Github checked!')

        chks = []
        if not chkDel: chks.append('Delete')
        if not chkRst: chks.append('Restore')

        return ChkInfo(False, 'Logic check failed!', f'Failed: {", ".join(chks)}')

    except Exception as e:
        return ChkInfo(False, 'Logic check error', str(e))

def checkSystem() -> SysStatus:
    return SysStatus(
        psql=psql(),
        immichPath=immichPath(),
        qdrant=qdrant(),
        immichLogic=immichLogic()
    )
