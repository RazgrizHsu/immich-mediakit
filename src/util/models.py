import os
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from conf import ks, envs
from util import log
from util.baseModel import BaseDictModel

lg = log.get(__name__)

@dataclass
class Nfy(BaseDictModel):
    msgs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def _init__(self, msgs): self.msgs = msgs

    def remove(self, nid):
        if nid in self.msgs: del self.msgs[nid]

    def info(self, msg, to=5000):
        lg.info(f"notify: {msg}")
        self._add(msg, "info", to)

    def success(self, msg, to=5000):
        lg.info(f"notify: {msg}")
        self._add(msg, "success", to)

    def warn(self, msg, to=8000):
        lg.warning(f"notify: {msg}")
        self._add(msg, "warning", to)

    def error(self, msg, to=0):
        lg.error(f"notify: {msg}")
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
    msg: Optional[str] = None

    def reset(self, withDone=True):
        self.id = self.name = self.cmd = self.msg = None
        self.args = {}


@dataclass
class Mdl(Cmd):
    msg: Optional[str|List[Any]] = None
    ok: bool = False

    def reset(self):
        self.id = self.msg = self.cmd = None
        self.ok = False
        self.args = {}

    def mkTsk(self):
        tsk = Tsk()

        tit = ks.pg.find(self.id)
        if tit:
            lg.info( f"tit.cmds({type(tit.cmds)}) => {tit.cmds}" )
            if not self.cmd in tit.cmds.values():
                lg.error(f'the MDL.cmd[{self.cmd}] not in [{tit.cmds}]')
                return None

            cmd = next(v for k, v in tit.cmds.items() if v == self.cmd)
            lg.info( f"cmd => type({type(cmd)}) v:{cmd}" )

            tsk.id = self.id
            tsk.name = tit.name
            tsk.cmd = self.cmd
            tsk.args |= self.args

            if hasattr( cmd, 'desc' ): tsk.msg = cmd.desc

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
class SimInfo(BaseDictModel):
    id: Optional[str] = None
    score: Optional[float] = None
    isSelf: Optional[bool] = False


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
    exifImageWidth: Optional[int] = None
    exifImageHeight: Optional[int] = None
    fileSizeInByte: Optional[int] = None
    orientation: Optional[str] = None
    dateTimeOriginal: Optional[str] = None
    modifyDate: Optional[str] = None
    lensModel: Optional[str] = None
    fNumber: Optional[float] = None
    focalLength: Optional[float] = None
    iso: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    fps: Optional[float] = None
    exposureTime: Optional[str] = None
    livePhotoCID: Optional[str] = None
    timeZone: Optional[str] = None
    projectionType: Optional[str] = None
    profileDescription: Optional[str] = None
    colorspace: Optional[str] = None
    bitsPerSample: Optional[int] = None
    autoStackId: Optional[str] = None
    rating: Optional[int] = None
    updatedAt: Optional[str] = None
    updateId: Optional[str] = None

    def toAvDict(self):
        return {k: v for k, v in self.toDict().items() if v is not None}

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
    isFavorite: Optional[int] = 0
    isVisible: Optional[int] = 0
    isArchived: Optional[int] = 0
    libraryId: Optional[str] = None
    localDateTime: Optional[str] = None
    thumbnail_path: Optional[str] = None
    preview_path: Optional[str] = None
    fullsize_path: Optional[str] = None
    jsonExif: Optional[AssetExif] = None
    isVectored: Optional[int] = 0
    simOk: Optional[int] = 0
    simInfos: List[SimInfo] = field(default_factory=list)

    # view only
    selected:Optional[bool] = False

    def getImagePath(self, photoQ=None):

        if photoQ == ks.db.fullsize:
            path = self.fullsize_path
        elif photoQ == ks.db.preview:
            path = self.preview_path
        else:
            path = self.thumbnail_path

        if not path: path = self.thumbnail_path

        if not path: raise RuntimeError( f"the thumbnail path is empty, assetId[{self.id}]" )

        return os.path.join(envs.immichPath, path)

@dataclass
class PageSim(BaseDictModel):
    avTabId: Optional[str] = None
    disableTabIds: List[str] = field(default_factory=list)
    isContinued: Optional[bool] = None

    assId: Optional[str] = None
    assets: List[Asset] = field(default_factory=list)

    selectIds: List[str] = field(default_factory=list)

    def reset(self):
        self.avTabId = self.isContinued = self.assId = None
        self.assets = []
        self.selectIds = []
        self.disableTabIds = []

@dataclass
class Pages(BaseDictModel):
    sim: PageSim = field(default_factory=PageSim)

@dataclass
class Now(BaseDictModel):
    usrs: List[Usr] = field(default_factory=list)
    usr: Optional[Usr] = None
    useType: Optional[str] = None
    photoQ: Optional[str] = None
    cntPic: int = 0
    cntVec: int = 0

    pg: Pages = field(default_factory=Pages)

    def switchUsr(self, usrId):
        if self.usrs:
            # lg.info( f"[switch] usr[{self.usrs[0]}]({type(self.usrs[0])})" )
            self.usr = next((u for u in self.usrs if u.id == usrId), None)
