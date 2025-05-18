from typing import Callable, Tuple

from dsh import htm, dbc, inp, out, ste, noUpd, getTriggerId
from util import log, models
from conf import Ks

lg = log.get(__name__)

IFnProg = Callable[[int, str, str], None]
IFnCall = Callable[[
    models.Nfy,
    models.Now,
    models.Tsk,
    IFnProg
], Tuple[models.Nfy, models.Now, str]]

mapFns: dict[str, IFnCall] = {}


class k:
    div = 'task-div'
    prg = 'task-progress'
    txt = 'task-txt'
    rst = 'task-result'
    btn = 'task-btn-close'


def render():
    return htm.Div([
        dbc.Row([
            dbc.Col(htm.P("", id=k.txt), width=10),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Progress(id=k.prg, value=0, animated=True, striped=True, style={"height": "30px"}, label="0%")
            ], width=12, className="mb-2"),
        ]),

        dbc.Row([
            dbc.Col(htm.Div(id=k.rst), width=10),
            dbc.Col([
                dbc.Button("close to continue", id=k.btn, className="btn-info", size="sm", disabled=True),
            ], width=2, className="text-end"),
        ]),

    ],
        id=k.div,
        style={'display': 'none'},
        className="mb-4 card cardbody p-3 border"
    )


# ========================================================================
def regBy(app):
    style_show = {'display': 'block'}
    style_none = {'display': 'none'}

    # ------------------------------------------------------------------------
    @app.callback(
        [
            out(k.div, "style"),
            out(k.txt, "children"),
        ],
        inp(Ks.store.tsk, "data"),
        prevent_initial_call=True
    )
    def task_status(dta_tsk):
        tsk = models.Tsk.fromStore(dta_tsk)

        hasTsk = tsk.name is not None

        style = style_show if hasTsk else style_none

        triggerId = getTriggerId()
        lg.info(f"[Task] Update display: {hasTsk} id[{tsk.id}] name[{tsk.name}] trigger[{triggerId}]")

        return style, tsk.name


    # ------------------------------------------------------------------------
    @app.callback(
        out(Ks.store.tsk, "data"),
        inp(k.btn, "n_clicks"),
        ste(Ks.store.tsk, "data"),
        prevent_initial_call=True
    )
    def onBtnTaskClose(_nclk, dta_tsk):
        tsk = models.Tsk.fromStore(dta_tsk)
        if tsk.id or tsk.name:
            tsk.reset()
            lg.info( "[task] close and reset.." )

        return tsk.toStore()

    # ------------------------------------------------------------------------
    @app.callback(
        [
            out(k.rst, "children"),
            out(k.prg, "value", allow_duplicate=True),
            out(Ks.store.tsk, "data", allow_duplicate=True),
            out(Ks.store.nfy, "data", allow_duplicate=True),
            out(Ks.store.now, "data", allow_duplicate=True),
        ],
        inp(Ks.store.tsk, "data"),
        ste(Ks.store.nfy, "data"),
        ste(Ks.store.now, "data"),
        background=True,
        running=[
            (out(k.btn, "disabled"), True, False),
        ],
        progress=[
            out(k.prg, "value"),
            out(k.prg, "label"),
            out(k.rst, "children"),
        ],
        progress_default=[0, "", "-- rst --"],
        prevent_initial_call=True
    )
    def onTasking(onUpdate, dta_tsk, dta_nfy, dta_now):
        # lg.info(f"[Task] Start execution... trigId[{trigId}] dta_tsk[{dta_tsk}]")

        tsk = models.Tsk.fromStore(dta_tsk)
        nfy = models.Nfy.fromStore(dta_nfy)
        now = models.Now.fromStore(dta_now)

        if not tsk.id:
            return noUpd, noUpd, noUpd, noUpd, noUpd

        lg.info(f"[Task] Start.. id[{tsk.id}] name[{tsk.name}] keyFn[{tsk.keyFn}]")

        fn = mapFns[tsk.keyFn]
        msg = None
        pct = 0

        def onUpd(percent, label, msg):
            lg.info(f"[Task] id[{tsk.id}] progress: {percent}% - {label} - {msg}")
            onUpdate([percent, label, msg])

        if fn:
            try:
                nfy, now, msg = fn(nfy, now, tsk, onUpd)
                pct = 100

                lg.info(f"[Task] done id[{tsk.id}]")
                tsk.id = None

            except Exception as e:
                msg = f"Task[{tsk.id}] execution failed: {str(e)}"
                lg.error(msg)
        else:
            pct = 50
            msg = f"task[{tsk.id}] NotFound task keyFn[{tsk.keyFn}]"
            lg.error( msg )

        return msg, pct, tsk.toStore(), nfy.toStore(), now.toStore()
