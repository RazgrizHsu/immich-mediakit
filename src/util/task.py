from typing import Callable, Tuple

from dsh import htm, dbc, inp, out, ste, noUpd
from util import log, models
from conf import Ks

lg = log.get(__name__)

IFnProg = Callable[[[str, int, str]], None]
IFnCall = Callable[[
    models.Nfy,
    models.Now,
    models.Tsk,
    IFnProg
], Tuple[models.Nfy, models.Now, str]]

mapFns: dict[str, IFnCall] = {}


class k:

    class id:
        div = 'task-div'
        prg = 'task-progress'
        txt = 'task-txt'
        rst = 'task-result'
        btn = 'task-btn-close'


def render():
    return htm.Div([
        dbc.Row([
            dbc.Col(htm.P("", id=k.id.txt), width=10),
            dbc.Col([
                dbc.Button("Ｘ", id=k.id.btn, className="btn-info", size="sm", disabled=True),
            ], width=2, className="text-end"),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Progress(
                    id=k.id.prg,
                    value=0,
                    animated=True,
                    striped=True,
                    style={"height": "30px"},
                    label="0%"
                ),
            ], width=12, className="mb-2"),
        ]),

        htm.Div(id=k.id.rst)
    ],
        id=k.id.div,
        style={'display': 'none'},
        className="mb-4 card cardbody p-3 border"
    )


#========================================================================
def regBy(app):
    style_show = {'display': 'block'}
    style_none = {'display': 'none'}

    #------------------------------------------------------------------------
    @app.callback(
        [
            out(k.id.div, "style"),
            out(k.id.txt, "children"),
        ],
        inp(Ks.store.tsk, "data"),
        prevent_initial_call=True
    )
    def update_txt(dta_tsk):
        tsk = models.Tsk.fromStore(dta_tsk)

        hasTsk = tsk.id is not None

        style = style_show if hasTsk else style_none
        title = tsk.name

        # lg.info(f"[Task] Update display: {hasTsk} id[{tsk.id}]")

        return style, title


    #------------------------------------------------------------------------
    @app.callback(
        out(Ks.store.tsk, "data"),
        inp(k.id.btn, "n_clicks"),
        ste(Ks.store.tsk, "data"),
        prevent_initial_call=True
    )
    def onBtnTaskClose(_nclk, dta_tsk):
        tsk = models.Tsk.fromStore(dta_tsk)
        if tsk.id:
            tsk.reset()
            lg.info( "重置tsk" )

        return tsk.toStore()

    #------------------------------------------------------------------------
    @app.callback(
        [
            out(k.id.rst, "children"),
            out(k.id.prg, "value", allow_duplicate=True),
            out(Ks.store.tsk, "data", allow_duplicate=True),
            out(Ks.store.nfy, "data", allow_duplicate=True),
            out(Ks.store.now, "data", allow_duplicate=True),
        ],
        inp(Ks.store.tsk, "data"),
        ste(Ks.store.nfy, "data"),
        ste(Ks.store.now, "data"),
        background=True,
        running=[
            (out(k.id.btn, "disabled"), True, False),
        ],
        progress=[
            out(k.id.prg, "value"),
            out(k.id.prg, "label"),
            out(k.id.rst, "children"),
        ],
        progress_default=[0, "", "-- rst --"],
        prevent_initial_call=True
    )
    def onTasking(onUpd, dta_tsk, dta_nfy, dta_now):
        # lg.info(f"[Task] Start execution... trigId[{trigId}] dta_tsk[{dta_tsk}]")

        tsk = models.Tsk.fromStore(dta_tsk)
        nfy = models.Nfy.fromStore(dta_nfy)
        now = models.Now.fromStore(dta_now)

        if not tsk.id:
            return noUpd, noUpd, noUpd, noUpd, noUpd

        lg.info(f"[Task] tsk: id[{tsk.id}] name[{tsk.name}] keyFn[{tsk.keyFn}]")

        fn = mapFns[tsk.keyFn]
        msg = None
        pct = 0

        if fn:
            try:
                nfy, now, msg = fn(nfy, now, tsk, onUpd)
                pct = 100

            except Exception as e:
                msg = f"Task[{tsk.id}] execution failed: {str(e)}"
                lg.error(msg)
        else:
            msg = f"Cannot find corresponding task keyFn[{tsk.keyFn}]"
            pct = 50

        return msg, pct, tsk.toStore(), nfy.toStore(), now.toStore()
