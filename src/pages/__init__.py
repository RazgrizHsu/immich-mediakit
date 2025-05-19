from dsh import out, inp, ste, noUpd, getTriggerId

from conf import Ks
from util import log, models

lg = log.get(__name__)

def regBy(app):
    @app.callback(
        [
            out(Ks.store.mdl, "data", allow_duplicate=True),
            out(Ks.store.tsk, "data", allow_duplicate=True),
            out(Ks.store.nfy, "data", allow_duplicate=True),
        ],
        [
            inp(Ks.store.mdl, "data"),
        ],
        [
            ste(Ks.store.now, "data"),
            ste(Ks.store.nfy, "data"),
        ],
        prevent_initial_call=True
    )
    def task_RunActs(dta_mdl, dta_now, dta_nfy):
        mdl = models.Mdl.fromStore(dta_mdl)

        tid = getTriggerId()
        # lg.info(f"[tsk] runActs tid[{tid}] mdl: ok[{mdl.ok}] id[{mdl.id}]")

        if not mdl.ok: return noUpd, noUpd, noUpd

        now = models.Now.fromStore(dta_now)
        nfy = models.Nfy.fromStore(dta_nfy)
        tsk = models.Tsk()

        if mdl.id == 'assets':
            # lg.info(f"[assets] Triggered: mdl: id[{mdl.id}] cmd[{mdl.cmd}] msg[{mdl.msg}]")

            tsk.id = 'assets'
            tsk.name = 'FetchAssets'
            if mdl.cmd == 'fetch':
                tsk.keyFn = 'fetch_assets_psql'
            else:
                tsk.keyFn = 'fetch_assets_clear'
            mdl.reset()
            nfy.info("Starting task: FetchAssets")

        if mdl.id == 'photovec' and mdl.ok:
            if mdl.cmd == 'process':
                tsk.id = 'photovec'
                tsk.name = 'Photo Vector Processing'
                tsk.keyFn = 'photoVec_ToVec'

                mdl.reset()
                nfy.info("Starting task: Photo Vector Processing")

            elif mdl.cmd == 'clear':
                tsk.id = 'photoVec_Clear'
                tsk.name = 'Clear Vectors'
                tsk.keyFn = 'photoVec_Clear'

                mdl.reset()
                nfy.info("Starting task: Clear Vectors")

        return mdl.toStore(), tsk.toStore(), nfy.toStore()
