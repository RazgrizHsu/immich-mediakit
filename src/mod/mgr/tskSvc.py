from typing import Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from util import log

from mod.mgr.tskMgr import BseTsk, TskMgr
from mod.models import Tsk, ITaskStore, IFnProg

lg = log.get(__name__)

mgr: Optional[TskMgr] = None

@dataclass
class DashTask(BseTsk):
    tsk: Optional[Tsk] = None
    fn: Optional[Callable] = None
    store: Optional[ITaskStore] = None

    # def __init__(self, tsk: models.Tsk, fn: Callable, store: ITaskStore):
    #     super().__init__(tsk.name)
    #     self.fn = fn
    #     self.store = store
    #     self.tsk = tsk

    @classmethod
    def mk(cls, tsk: Tsk, fn: Callable, store: ITaskStore):
        return cls(
            name=tsk.name,
            tsk=tsk,
            fn=fn,
            store=store
        )

    def run(self, doReport: Optional[IFnProg] = None) -> Any:

        #------------------------------------
        # adapter
        #------------------------------------
        def report(pct: int, msg: str):
            if doReport: doReport(pct, f"{msg}")
            # lg.info(f"[Task] id[{self.tskId}] progress: {percent}% - {label} - {msg}")

        #------------------------------------
        try:
            sto = self.fn(report, self.store)

            # always return store
            return sto if sto else self.store

        except Exception as e:
            lg.error(f"[Task] name[{self.name}] call fn failed: {str(e)}")
            raise

def init(port: Optional[int] = None, forceInit=False):
    import os
    if forceInit or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        global mgr
        if not mgr:
            try:
                if port is None:
                    from conf import envs
                    port = int(envs.mkitPortWs)
                mgr = TskMgr(port=port)
                mgr.start()
                lg.info(f"[TskMgr] Started on port {port}")
            except Exception as e:
                lg.error(f"[TskMgr] Init Failed: {str(e)}")
                raise RuntimeError(f"[TskMgr] Start failed, port[{port}]: {str(e)}")
        return mgr
    else:
        lg.warn("[TskMgr] Ignore init..")

def stop():
    global mgr
    if mgr:
        mgr.stop()
        mgr = None
        lg.info("[TskMgr] Stopped")

def mkTask(tsk: Tsk, fn: Callable, sto: ITaskStore) -> str:
    if not mgr: raise RuntimeError("TskMgr not initialized")

    tskSn = mgr.regBy(DashTask.mk(tsk, fn, sto))

    return tskSn

def runBy(tskId: str) -> bool:
    if not mgr: raise RuntimeError("TskMgr not initialized")

    return mgr.run(tskId)


def getResultBy(tskId: str) -> Optional[ITaskStore]:
    if not mgr: return None

    ti = mgr.getInfo(tskId)
    if ti and tskId in mgr.tsks:
        dTsk = mgr.tsks[tskId]
        if isinstance(dTsk, DashTask):
            return dTsk.store

    lg.error(f"[TskSvc] failed get result from tskId[{tskId}]")
    return None
