
import os
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

from .base import BaseDictModel
from .mods import Pager
from .data import Asset




@dataclass
class PgSim(BaseDictModel):
    pagerPnd: Optional[Pager] = None
    activeTab: Optional[str] = "tab-current"



    assAid: int = 0
    assCur: List[Asset] = field(default_factory=list)

    assPend: List[Asset] = field(default_factory=list)

    assFromUrl: Optional[Asset] = None

    fspSize: bool = False
    fspW: bool = False
    fspH: bool = False

    def clearNow(self):
        self.assAid = 0
        self.assFromUrl = None
        self.assCur.clear()

    def clearAll(self):
        self.clearNow()
        self.assPend.clear()



@dataclass
class Now(BaseDictModel):
    sim: PgSim = field(default_factory=PgSim)
