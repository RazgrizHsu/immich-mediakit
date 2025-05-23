from dsh import out, inp, ste, noUpd, callback, getTriggerId

from conf import ks
from util import log
from mod import models

lg = log.get(__name__)

@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
    ],
    [
        inp(ks.sto.mdl, "data"),
    ],
    [
        ste(ks.sto.now, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def task_RunActsFromModal(dta_mdl, dta_now, dta_nfy):
    mdl = models.Mdl.fromStore(dta_mdl)

    tid = getTriggerId()
    # lg.info(f"[tsk] runActs tid[{tid}] mdl: ok[{mdl.ok}] id[{mdl.id}]")

    if not mdl.ok: return noUpd, noUpd, noUpd

    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)
    tsk = mdl.mkTsk()

    if tsk:
        # lg.info(f"[assets] Triggered: mdl: id[{mdl.id}] cmd[{mdl.cmd}] msg[{mdl.msg}]")
        msg = tsk.msg if tsk.msg else tsk.id
        nfy.info( f"Start task: {msg}" )
        mdl.reset()

    return mdl.toStore(), tsk.toStore(), nfy.toStore()
