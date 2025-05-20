from dsh import out, inp, ste, noUpd, getTriggerId

from conf import ks
from util import log, models

lg = log.get(__name__)

def regBy(app):
    @app.callback(
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
    def task_RunActs(dta_mdl, dta_now, dta_nfy):
        mdl = models.Mdl.fromStore(dta_mdl)

        tid = getTriggerId()
        # lg.info(f"[tsk] runActs tid[{tid}] mdl: ok[{mdl.ok}] id[{mdl.id}]")

        if not mdl.ok: return noUpd, noUpd, noUpd

        now = models.Now.fromStore(dta_now)
        nfy = models.Nfy.fromStore(dta_nfy)
        tsk = models.Tsk()

        if mdl.id == ks.pg.fetch:
            # lg.info(f"[assets] Triggered: mdl: id[{mdl.id}] cmd[{mdl.cmd}] msg[{mdl.msg}]")

            mdl.msg

            tsk.id = ks.pg.fetch
            tsk.name = 'FetchAssets'
            tsk.cmd = mdl.cmd

            mdl.reset()
            nfy.info("Starting task: FetchAssets")

        if mdl.id == 'photovec':
            if mdl.cmd == 'process':
                tsk.id = 'photovec'
                tsk.name = 'Photo Vector Processing'
                tsk.cmd = 'photoVec_ToVec'

                mdl.reset()
                nfy.info("Starting task: Photo Vector Processing")

            elif mdl.cmd == 'clear':
                tsk.id = 'photoVec_Clear'
                tsk.name = 'Clear Vectors'
                tsk.cmd = 'photoVec_Clear'

                mdl.reset()
                nfy.info("Starting task: Clear Vectors")

        elif mdl.id == ks.pg.similar:
            if mdl.cmd == 'process':
                tsk.id = 'pgs_similar'
                tsk.name = 'PGS Similar'

        return mdl.toStore(), tsk.toStore(), nfy.toStore()
