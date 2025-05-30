from dsh import htm, dcc, dbc, inp, out, ste, callback
from mod import models
from conf import ks, envs
from db import psql
import core

class k:
    connInfo = 'div-conn-info'
    sideState = 'div-side-state'
    cardEnv = 'env-card-body'
    cardCnt = 'cache-card-body'

def layout():
    return htm.Div([
        dbc.Card([
            dbc.CardHeader("env"),
            dbc.CardBody(id=k.cardEnv, children=[
                htm.Div( "connecting..." )
            ])
        ], className="mb-2"),

        dbc.Card([
            dbc.CardHeader("Cache Count"),
            dbc.CardBody(id=k.cardCnt, children=[
                htm.Div( "counting..." )
            ])
        ]),
    ],
        className="sidebar"
    )


@callback(
    [
        out(k.cardEnv, "children"),
        out(k.cardCnt, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True),
    ],
    inp(ks.sto.init, "children"),
    inp(ks.sto.cnt, "data"),
    ste(ks.sto.nfy, "data"),

    prevent_initial_call="initial_duplicate",
)
def onUpdateSideBar(_trigger, dta_count, dta_nfy):
    cnt = models.Cnt.fromDict(dta_count)
    nfy = models.Nfy.fromDict(dta_nfy)

    testDA = psql.testAssetsPath()
    testOk = testDA.startswith("OK")

    chkDel = core.checkLogicDelete()
    chkRst = core.checkLogicRestore()

    logicOk = chkDel and chkRst

    if not logicOk:
        if not chkDel:
            nfy.error([
                f"[system]", htm.Br(),
                f" the immich source code check failed,", htm.Br(),
                f" the Delete logic may changed, please check it before usage system"
            ])
        if not chkRst:
            nfy.error([
                f"[system]", htm.Br(),
                f" the immich source code check failed,", htm.Br(),
                f" the Restore logic may changed, please check it before usage system"
            ])

    if testDA and not testDA.startswith("OK"):
        nfy.error(["[system] access to IMMICH_PATH is Failed,",htm.Br(),htm.Small(f"{testDA}")])

    envRows = [
        dbc.Row([
            dbc.Col([htm.Small("logic check:")], width=5, className=""),
            dbc.Col([
                htm.Span(
                    f"Github checked!", className="tag info"
                ) if logicOk else htm.Span
                    (
                    f"Fail!!", className="tag"
                )
            ]),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col([htm.Small("Path Test:")], width=5, className=""),
            dbc.Col([
                htm.Span(
                    f"OK", className="tag info"
                ) if testOk else htm.Span
                    (
                    f"Failed", className="tag"
                )
            ]),
        ], className="mb-2"),
    ]

    cacheRows = [
        dbc.Row([
            dbc.Col(htm.Small("Photo Count", className="d-inline-block me-2"), width=6),
            dbc.Col(dbc.Alert(f"{cnt.ass}", color="info", className="py-0 px-2 mb-2 text-center")),
        ]),
        dbc.Row([
            dbc.Col(htm.Small("Vector Count", className="d-inline-block me-2"), width=6),
            dbc.Col(dbc.Alert(f"{cnt.vec}", color="info", className="py-0 px-2 mb-2 text-center")),
        ]),
    ]

    return envRows, cacheRows, nfy.toDict()
