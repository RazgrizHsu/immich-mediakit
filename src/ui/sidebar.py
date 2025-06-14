from dsh import htm, dcc, dbc, inp, out, ste, cbk
from mod import models
from conf import ks, envs
from db import psql
import immich
import torch
import conf

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

    testDA = psql.testAssetsPath()
    testOk = testDA.startswith("OK")

    chkDel = immich.checkLogicDelete()
    chkRst = immich.checkLogicRestore()

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

    # 獲取GPU設備信息
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
            htm.Small("Logic Check:"),
            htm.Span(
                f"Github checked!", className="tag info"
            ) if logicOk else htm.Span
                (
                f"Fail!!", className="tag"
            )
        ], className="mb-2"),
        htm.Div([
            htm.Small("Path Test:"),
            htm.Span(
                f"OK", className="tag info"
            ) if testOk else htm.Span
                (
                f"Failed", className="tag"
            )
        ], className="mb-2"),
        htm.Div([
            htm.Small("device:"),
            htm.Span(dvcInfo, className=dvcStyle, title=f"Device: {conf.device}")
        ], className="mb-2"),
    ]

    sizeL = 5

    cacheRows = [
        dbc.Row([
            dbc.Col(htm.Small("Photo Count", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(dbc.Alert(f"{cnt.ass}", color="info", className="py-0 px-2 mb-2 text-center")),
        ]),
        dbc.Row([
            dbc.Col(htm.Small("Vector Count", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(dbc.Alert(f"{cnt.vec}", color="info", className="py-0 px-2 mb-2 text-center")),
        ]),

        dbc.Row([
            dbc.Col(htm.Small("NotSearch", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(
                htm.Div([
                    htm.Span(f"{cnt.simOk}", className="tag lg second txt-c"),
                    htm.Span(f"{cnt.simNo}", className="tag lg info txt-c")
                ],
                    style={ "display":"grid", "gridTemplateColumns":"1fr 1fr" }
                )
            ) ,
        ]),
        dbc.Row([
            dbc.Col(htm.Small("Pending", className="d-inline-block me-2"), width=sizeL),
            dbc.Col(dbc.Alert(f"{cnt.simPnd}", color="info", className="py-1 px-2 mb-2 text-center")),
        ]),
    ]

    return envRows, cacheRows, nfy.toDict()
