import os
from dataclasses import dataclass
from typing import List, Union

from conf import envs
from util import log

import db
import immich

lg = log.get(__name__)

@dataclass
class ChkInfo:
    ok: bool
    msg: Union[str, List[str]] = ''

@dataclass
class SysSte:
    ver: ChkInfo
    psql: ChkInfo
    path: ChkInfo
    vec: ChkInfo
    logic: ChkInfo

    @property
    def allOk(self) -> bool:
        return all(check.ok for check in [self.psql, self.path, self.vec, self.logic])


def ver() -> ChkInfo:
    try:

        return ChkInfo(True, ['Qdrant connection OK', f'URL: {envs.qdrantUrl}'])

    except Exception as e:
        return ChkInfo(False, ['Qdrant check failed', str(e)])

def qdrant() -> ChkInfo:
    try:
        if not envs.qdrantUrl: return ChkInfo(False, 'Qdrant URL not configured')

        db.vecs.init()

        return ChkInfo(True, ['Qdrant connection OK', f'URL: {envs.qdrantUrl}'])

    except Exception as e:
        return ChkInfo(False, ['Qdrant check failed', str(e)])

def psql() -> ChkInfo:
    try:
        if not all([envs.psqlHost, envs.psqlPort, envs.psqlDb, envs.psqlUser]):
            return ChkInfo(False, ['PostgreSQL settings incomplete', 'Missing required connection parameters'])

        if not db.psql.init(): return ChkInfo(False, ['Cannot connect to PostgreSQL', 'Connection test failed'])

        return ChkInfo(True, ['IMMICH_PATH accessible', f'Path: {envs.immichPath}'])
    except Exception as e:
        return ChkInfo(False, ['PostgreSQL check failed', str(e)])

def immichPath() -> ChkInfo:
    try:
        if not envs.immichPath: return ChkInfo(False, 'IMMICH_PATH not configured')

        if not os.path.exists(envs.immichPath): return ChkInfo(False, ['IMMICH_PATH does not exist', f'Path: {envs.immichPath}'])

        if not os.path.isdir(envs.immichPath): return ChkInfo(False, ['IMMICH_PATH is not a directory', f'Path: {envs.immichPath}'])

        if not os.access(envs.immichPath, os.R_OK): return ChkInfo(False, ['IMMICH_PATH is not readable', f'Path: {envs.immichPath}'])

        rst = db.psql.testAssetsPath()
        if rst == "No Assets": return ChkInfo(True)

        if "OK" not in rst:
            return ChkInfo(False, ['Asset path test failed', *rst])

        return ChkInfo(True)

    except Exception as e:
        return ChkInfo(False, ['IMMICH_PATH check failed', str(e)])

def immichLogic() -> ChkInfo:
    try:
        checks = [
            (immich.checkLogicDelete(), "Delete logic"),
            (immich.checkLogicRestore(), "Restore logic"),
            (immich.checkAlbAssAdd(), "Album assign add logic"),
            (immich.checkAlbumAssDel(), "Album assign delete logic")
        ]

        failed = [desc for ok, desc in checks if not ok]

        if failed:
            msgs = ["[system]"]
            for desc in failed:
                msgs.append(f"❌ {desc} check failed.")

            msgs += [
                "The Operation logic may have changed.",
                "Please **DO NOT use the system** and **check the GitHub repository** for updates immediately.",
                "If no updates are available, please report this issue to raz."
            ]

            return ChkInfo(False, msgs)

        return ChkInfo(True, 'Github checked!')

    except Exception as e:
        return ChkInfo(False, ['Logic check error', str(e)])


def checkSystem() -> SysSte:
    return SysSte(
        ver=ver(),
        psql=psql(),
        path=immichPath(),
        vec=qdrant(),
        logic=immichLogic()
    )
