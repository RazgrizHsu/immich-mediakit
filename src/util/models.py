import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

from util import log
from util.baseModel import BaseDictModel
from conf import ks

lg = log.get(__name__)

@dataclass
class Nfy(BaseDictModel):
    msgs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def _init__(self, msgs): self.msgs = msgs

    def remove(self, nid):
        if nid in self.msgs: del self.msgs[nid]

    def info(self, msg, to=3000):
        lg.info(msg)
        self._add(msg, "info", to)

    def success(self, msg, to=5000):
        lg.info(msg)
        self._add(msg, "success", to)

    def warn(self, msg, to=8000):
        lg.warning(msg)
        self._add(msg, "warning", to)

    def error(self, msg, to=0):
        lg.error(msg)
        self._add(msg, "danger", to)

    def _add(self, msg, typ, to):
        nid = str(uuid.uuid4())
        self.msgs[nid] = {'message': msg, 'type': typ, 'timeout': to}


@dataclass
class Cmd(BaseDictModel):
    id: Optional[str] = None
    cmd: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tsk(Cmd):
    name: Optional[str] = None

    def reset(self, withDone=True):
        self.id = self.name = self.cmd = None
        self.args = {}


@dataclass
class Mdl(Cmd):
    msg: Optional[str] = None
    ok: bool = False

    def reset(self):
        self.id = self.msg = self.cmd = None
        self.ok = False
        self.args = {}

    def mkTsk(self):
        tsk = Tsk()

        tit = ks.pg.find(self.id)
        if tit:
            if not self.id in tit.cmds:
                lg.error(f'the MDL.id[{self.id}] not in [{tit}]')
                return None

            cmds = tit.cmds.keys()
            tsk.id = self.id
            tsk.name = tit.name
            tsk.cmd = self.cmd
            tsk.args |= self.args
            return tsk
        else:
            return None


@dataclass
class ProcessInfo(BaseDictModel):
    total: int = 0
    skip: int = 0
    error: int = 0
    done: int = 0


@dataclass
class Usr(BaseDictModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    key: Optional[str] = None


@dataclass
class AssetExif(BaseDictModel):
    make: Optional[str] = None
    model: Optional[str] = None
    orientation: Optional[int] = None
    exposureTime: Optional[str] = None
    fNumber: Optional[float] = None
    focalLength: Optional[float] = None
    iso: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dateTimeOriginal: Optional[str] = None
    lensModel: Optional[str] = None

@dataclass
class Asset(BaseDictModel):
    autoId: Optional[int] = None
    id: Optional[str] = None
    ownerId: Optional[str] = None
    deviceId: Optional[str] = None
    type: Optional[str] = None
    originalFileName: Optional[str] = None
    fileCreatedAt: Optional[str] = None
    fileModifiedAt: Optional[str] = None
    isFavorite: Optional[int] = None
    isVisible: Optional[int] = None
    isArchived: Optional[int] = None
    libraryId: Optional[str] = None
    localDateTime: Optional[str] = None
    thumbnail_path: Optional[str] = None
    preview_path: Optional[str] = None
    fullsize_path: Optional[str] = None
    jsonExif: Optional[AssetExif] = None
    isVectored: int = 0
    simOk: int = 0
    simIds: List[str] = field(default_factory=list)

    def getImagePath(self, photoQ=None):
        import os
        from conf import ks, envs

        if photoQ == ks.db.fullsize:
            path = self.fullsize_path
        elif photoQ == ks.db.preview:
            path = self.preview_path
        else:
            path = self.thumbnail_path

        return os.path.join(envs.immichPath, path)


@dataclass
class Now(BaseDictModel):
    usrs: List[Usr] = field(default_factory=list)
    usr: Optional[Usr] = None
    useType: Optional[str] = None
    photoQ: Optional[str] = None
    cntPic: int = 0
    cntVec: int = 0

    selectIds: List[str] = field(default_factory=list)

    assets: List[Asset] = field(default_factory=list)


    def switchUsr(self, usrId):
        if self.usrs:
            # lg.info( f"[switch] usr[{self.usrs[0]}]({type(self.usrs[0])})" )
            self.usr = next((u for u in self.usrs if u.id == usrId), None)
