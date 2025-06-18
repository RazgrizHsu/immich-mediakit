from conf import ks, envs
from dsh import dash, htm, dbc, dcc
from util import log

from ui import cardSets

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/',
    title=f"{ks.title}: " + 'System Settings',
)

def getStatusClass(ok: bool) -> str:
    if not ok: return 'bg-danger text-white'
    return ''

def getStatusIcon(ok: bool):
    if ok: return htm.I(className="bi bi-check-circle-fill text-success me-2")
    return htm.I(className="bi bi-x-circle-fill text-danger me-2")

#========================================================================
def layout():
    import ui
    import chk
    sysStatus = chk.checkSystem()

    return ui.renderBody([
        #====== top start =======================================================

        htm.Div([
            htm.H3(f"{ks.pg.setting.name}"),
            htm.Small(f"{ks.pg.setting.desc}", className="text-muted")
        ], className="body-header"),

        htm.Div([
            htm.Div([
                dbc.Card([
                    dbc.CardHeader([
                        "System Configuration"
                    ]),
                    dbc.CardBody([

                        htm.Div([

                            htm.Div([
                                htm.Div(htm.Small("MediaKit Data Path", className="text-muted"), className="d-flex align-items-center"),
                                htm.Div(envs.mkitData or htm.Span("(Not configured)", className="text-warning"), className="fw-semibold text-break"),
                            ], className="row mb-3"),

                            htm.Div([
                                htm.Div([
                                    getStatusIcon(sysStatus.immichLogic.ok),
                                    htm.Small("Immich Logic Check", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div([
                                    htm.Span("GitHub Repository Check", className="fw-semibold me-2"),
                                    htm.Span(sysStatus.immichLogic.msg, className="small")
                                ], className="fw-semibold")
                            ], className=f"row mb-3 p-2 rounded {getStatusClass(sysStatus.immichLogic.ok)}"),

                            htm.Div([
                                htm.Div([
                                    getStatusIcon(sysStatus.psql.ok),
                                    htm.Small("PostgreSQL Connection", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div([
                                    htm.Span(f"{envs.psqlHost}:{envs.psqlPort}", className="fw-semibold me-2"),
                                    htm.Span(sysStatus.psql.msg, className="small")
                                ], className="fw-semibold")
                            ], className=f"row mb-3 p-2 rounded {getStatusClass(sysStatus.psql.ok)}"),

                            htm.Div([
                                htm.Div([
                                    getStatusIcon(sysStatus.immichPath.ok),
                                    htm.Small("Immich Root Path", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div([
                                    htm.Span(envs.immichPath or "(Not configured)", className="fw-semibold text-break me-2"),
                                    htm.Span(sysStatus.immichPath.msg, className="small")
                                ], className="fw-semibold")
                            ], className=f"row mb-3 p-2 rounded {getStatusClass(sysStatus.immichPath.ok)}"),

                            htm.Div([
                                htm.Div([
                                    getStatusIcon(sysStatus.qdrant.ok),
                                    htm.Small("Qdrant URL", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div([
                                    htm.Span(envs.qdrantUrl or "(Not configured)", className="fw-semibold text-break me-2"),
                                    htm.Span(sysStatus.qdrant.msg, className="small")
                                ], className="fw-semibold")
                            ], className=f"row mb-3 p-2 rounded {getStatusClass(sysStatus.qdrant.ok)}"),


                        ])
                    ])
                ], className="border-0 shadow-sm")
            ], className="col-lg-10 mb-4"),


            htm.Div([

                cardSets.renderThreshold(),

                cardSets.renderCard(),


            ], className="border-0 shadow-sm")

        ], className="row"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #====== bottom end ======================================================
    ])
