from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from util.baseModel import BaseDictModel, Json

from util import log

lg = log.get(__name__)


@dataclass
class usr(BaseDictModel):
	id: Optional[str] = None
	name: Optional[str] = None
	email: Optional[str] = None
	apiKey: Optional[str] = None

@dataclass
class Now(BaseDictModel):
	usrId: Optional[str] = None
	useType: Optional[str] = None

	cntPic: int = 0
	cntVec: int = 0

	# Used to let frontend select usr
	usrs: List[usr] = field(default_factory=list)

	def getUserName(self, usrId):
		for usr in self.usrs:
			if usr.id == usrId: return usr.name
		return None


@dataclass
class AppState(BaseDictModel):
	current_page: str = "home"
	selected_items: List[str] = field(default_factory=list)
	filters: Dict[str, Any] = field(default_factory=dict)
	last_updated: datetime = field(default_factory=datetime.now)


import uuid


@dataclass
class Nfy(BaseDictModel):
	msgs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

	def _init__(self, msgs):
		self.msgs = msgs

	def remove(self, nid):
		if nid in self.msgs: del self.msgs[nid]

	def info(self, message, timeout=5000):
		lg.info( message )
		self._add(message, "info", timeout)

	def success(self, message, timeout=5000):
		lg.info( message )
		self._add(message, "success", timeout)

	def warn(self, message, timeout=8000):
		lg.warn( message )
		self._add(message, "warning", timeout)

	def error(self, message, timeout=0):
		lg.error( message )
		self._add(message, "danger", timeout)

	def _add(self, message, kind, timeout):
		nid = str(uuid.uuid4())
		self.msgs[nid] = {
			'message': message,
			'type': kind,
			'timeout': timeout
		}


@dataclass
class Tsk(BaseDictModel):
	id: Optional[str] = None
	name: Optional[str] = None
	keyFn: Optional[str] = None
	args: Dict[str, Any] = field(default_factory=dict)

	def reset(self, withDone=True):
		self.id = self.name = self.keyFn = None
		self.args = {}

@dataclass
class Mdl(BaseDictModel):
	id: Optional[str] = None
	msg: Optional[str] = None
	ok: bool = False

	cmd: Optional[str] = None
	args: Dict[str, Any] = field(default_factory=dict)

	def reset(self):
		self.id = self.msg = self.cmd = None
		self.ok = False
		self.args = {}


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
	jsonExif: Optional[str] = None
	exifInfo: Json = field(default_factory=Json)
	isVectored: int = 0
