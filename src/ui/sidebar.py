from dsh import htm, dbc, inp, out, ste, callback
from mod import models
from conf import ks, envs
from db import psql


class k:
    sideState = 'div-side-state'
    connInfo = 'div-conn-info'

def layout():
    return htm.Div(
        htm.Div(id=k.sideState),
        className="sidebar")



@callback(
    [
        out(k.sideState, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True ),
    ],
    inp(ks.sto.init, "children"),
    inp(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data" ),
    #
    prevent_initial_call="initial_duplicate",
)
def onUpdateSideBar(_trigger, dta_now, dta_nfy):
    now = models.Now.fromDict(dta_now)
    nfy = models.Nfy.fromDict(dta_nfy)

    testIP = envs.immichPath if envs.immichPath else '--none--'
    testDA = psql.testAssetsPath()

    if testDA and not testDA.startswith("OK"):
        nfy.warn( f"[system] the direct access to IMMICH_PATH is Failed[ {testDA} ]" )

    htmCnts = htm.Div([
        dbc.Card([
            dbc.CardHeader("env"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([htm.Small("IMMICH_PATH:")], width=5, className=""),
                    dbc.Col([
                        htm.Span(f"{testIP}", className="tag" ),
                    ]),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([htm.Small("Path Test:")], width=5, className=""),
                    dbc.Col([
                        htm.Span(
                            f"{testDA}", className="tag ok"
                        ) if testDA.startswith("OK") else htm.Span
                        (
                            f"{testDA}", className="tag"
                        )
                    ]),
                ], className="mb-2"),
            ])
        ], className="mb-2"),

        dbc.Card([
            dbc.CardHeader("Cache Count"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(htm.Small("Photo Count", className="d-inline-block me-2"), width=5),
                    dbc.Col(dbc.Alert(f"{now.cntPic}", color="info", className="py-0 px-2 mb-2")),
                ]),
                dbc.Row([
                    dbc.Col(htm.Small("Vector Count", className="d-inline-block me-2"), width=5),
                    dbc.Col(dbc.Alert(f"{now.cntVec}", color="info", className="py-0 px-2 mb-2")),
                ]),
            ])
        ]),

    ])

    return htmCnts, nfy.toDict()

def test():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #====== bottom end ======================================================
    ])
