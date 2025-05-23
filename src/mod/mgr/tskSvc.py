from typing import Any, Callable, Optional, Tuple
import uuid

from mod.mgr.tskMgr import BseTsk, TskMgr
from util import log
from mod import models

lg = log.get(__name__)

mgr: Optional[TskMgr] = None

class DashTask(BseTsk):
    def __init__(self, tskId: str, name: str, cmd: str, fn: Callable, nfy: models.Nfy, now: models.Now, tsk: models.Tsk):
        super().__init__(tskId, name, hasCB=True)
        self.cmd = cmd
        self.fn = fn
        self.nfy = nfy
        self.now = now
        self.tsk = tsk
        self.origTskId = tsk.id

    def execute(self, callback: Optional[Callable[[int, str], None]] = None) -> Any:
        def onUpd(percent: int, label: str, msg: str):
            if callback: callback(percent, f"{label} - {msg}")
            lg.info(f"[Task] id[{self.tskId}] progress: {percent}% - {label} - {msg}")

        try:
            oid = self.tsk.id
            self.tsk.id = self.origTskId

            nfy, now, msg = self.fn(self.nfy, self.now, self.tsk, onUpd)

            self.tsk.id = oid

            self.nfy = nfy
            self.now = now
            return msg
        except Exception as e:
            lg.error(f"[Task] id[{self.tskId}] failed: {str(e)}")
            raise

def init(port: int = 8765, forceInit = False):
    import os
    if forceInit or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        global mgr
        if not mgr:
            try:
                mgr = TskMgr(port=port)
                mgr.start()
                lg.info(f"[TskMgr] Started on port {port}")
            except Exception as e:
                lg.error( f"[TskMgr] Init Failed: {str(e)}")
                raise RuntimeError(f"[TskMgr] Start failed, port[{port}]: {str(e)}")
        return mgr
    else:
        lg.warn( "[TskMgr] Ignore init.." )

def stop():
    global mgr
    if mgr:
        mgr.stop()
        mgr = None
        lg.info("[TskMgr] Stopped")

def mkTask(name: str, cmd: str, fn: Callable, nfy: models.Nfy, now: models.Now, tsk: models.Tsk) -> str:
    if not mgr: raise RuntimeError("TskMgr not initialized")

    tskId = str(uuid.uuid4())
    task = DashTask(tskId, name, cmd, fn, nfy, now, tsk)
    mgr.regBy(task)

    tsk.id = tskId
    tsk.name = name
    tsk.cmd = cmd

    return tskId

def runBy(tskId: str) -> bool:
    if not mgr: raise RuntimeError("TskMgr not initialized")

    return mgr.run(tskId)

def cancelBy(tskId: str) -> bool:
    if not mgr: raise RuntimeError("TskMgr not initialized")

    return mgr.cancel(tskId)

def getResultBy(tskId: str) -> Tuple[Optional[models.Nfy], Optional[models.Now], Optional[str]]:
    if not mgr: return None, None, None

    task_info = mgr.getInfo(tskId)
    if task_info and tskId in mgr.tsks:
        task = mgr.tsks[tskId]
        if isinstance(task, DashTask): return task.nfy, task.now, task_info.result

    return None, None, None
