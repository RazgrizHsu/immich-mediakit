from dsh import htm, dcc, dbc, inp, out, ste, cbk
from mod import models
from conf import ks, envs
from db import psql
import immich
import torch
import conf
import chk

class k:
    connInfo = 'div-conn-info'
    sideState = 'div-side-state'
    cardEnv = 'env-card-body'
    cardCnt = 'cache-card-body'

def getStatusIcon(ok: bool):
    if ok: return htm.I(className="bi bi-check-circle-fill text-success")
    return htm.I(className="bi bi-x-circle-fill text-danger")

def layout():
    return htm.Div([
        dbc.Card([
            dbc.CardHeader("env"),
            dbc.CardBody(id=k.cardEnv, children=[
                htm.Div( "connecting..." )
            ], className="igrid divRows")
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


@cbk(
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

    rst = chk.checkSystem()

    if not rst.immichLogic.ok:
        if 'Delete' in rst.immichLogic.details:
            nfy.error([
                f"[system]", htm.Br(),
                f" the immich source code check failed,", htm.Br(),
                f" the Delete logic may have changed.", htm.Br(),
                f" Please **DO NOT use the system** and **check the GitHub repository** for updates immediately.", htm.Br(),
                f" If no updates are available, please report this issue to raz."
            ])
        if 'Restore' in rst.immichLogic.details:
            nfy.error([
                f"[system]", htm.Br(),
                f" the immich source code check failed,", htm.Br(),
                f" the Restore logic may have changed.", htm.Br(),
                f" Please **DO NOT use the system** and **check the GitHub repository** for updates immediately.", htm.Br(),
                f" If no updates are available, please report this issue to raz"
            ])

    if not rst.allOk:
        errs = []
        if not rst.psql.ok: errs.append(f"PostgreSQL: {rst.psql.msg}")
        if not rst.immichPath.ok: errs.append(f"Immich Path: {rst.immichPath.msg}")
        if not rst.qdrant.ok: errs.append(f"Qdrant: {rst.qdrant.msg}")

        if errs:
            nfy.error([
                f"[system errors]", htm.Br(),
                *[htm.Div([f"• {detail}", htm.Br()]) for detail in errs]
            ])

    dvcType = conf.device.type
    if dvcType == 'cuda':
        try:
            gpuNam = torch.cuda.get_device_name(0)
            gpuMem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            dvcInfo = f"NVIDIA {gpuNam[:20]}... ({gpuMem:.1f}GB)"
            dvcStyle = "tag info"
        except:
            dvcInfo = "CUDA GPU"
            dvcStyle = "tag info"
    elif dvcType == 'mps':
        try:
            import platform
            processor = platform.processor() or "Apple Silicon"
            import psutil
            cMem = psutil.virtual_memory().total / (1024**3)
            dvcInfo = f"Apple {processor} ({cMem:.1f}GB)"
            dvcStyle = "tag info"
        except:
            dvcInfo = "Apple MPS"
            dvcStyle = "tag info"
    else:
        import multiprocessing
        cCpu = multiprocessing.cpu_count()
        dvcInfo = f"CPU ({cCpu} cores)"
        dvcStyle = "tag"

    envRows = [
        htm.Div([
            htm.Small("system:"),
            htm.Span([
                getStatusIcon(rst.allOk),
                " all ok" if rst.allOk else " ERROR"
            ], className="tag info" if rst.allOk else "tag red")
        ], className="mb-2"),
        htm.Div([
            htm.Small("device:"),
            htm.Span(dvcInfo, className=dvcStyle, title=f"Device: {conf.device}")
        ], className="mb-2"),
    ]

    sizeL = 3

    cacheRows = [
        dbc.Row([
            dbc.Col(htm.Small("Assets", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(htm.Span(f"{cnt.ass}", className="tag px-3 mb-2 txt-c")),
        ]),
        dbc.Row([
            dbc.Col(htm.Small("Vectors", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(htm.Span(f"{cnt.vec}", className="tag px-3 mb-2 txt-c")),
        ], className="mb-1"),

        dbc.Row([
            dbc.Col(htm.Small("Resolve", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(
                htm.Div([
                    htm.Span(f"{cnt.simOk}", className="tag info txt-c"), " / ",
                    htm.Span(f"{cnt.simNo}", className="tag second txt-c")
                ],
                    style={ "display":"grid", "gridTemplateColumns":"1fr auto 1fr" }
                )
            ) ,
        ]),
        dbc.Row([
            dbc.Col(htm.Small("Pending", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(htm.Span(f"{cnt.simPnd}", className="tag blue px-3 mb-2 text-center")),
        ]),
    ]

    return envRows, cacheRows, nfy.toDict()
