
from conf import ks, envs
from dsh import dash, htm, dbc, dcc
from util import log
import db

from ui import cardSets

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/',
    title=f"{ks.title}: " + 'System Settings',
)

#========================================================================
def layout():
    import ui
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

                                    htm.Div([
                                        htm.Div(htm.Small("Hostname", className="text-muted"), className="d-flex align-items-center"),
                                        htm.Span(envs.psqlHost or htm.Span("(Not configured)", className="text-warning"), className="fw-semibold"),
                                        htm.Span(envs.psqlPort or "5432", className="fw-semibold")
                                    ]),

                                ], className="col-md-6"),

                                htm.Div([
                                    htm.Div([htm.Small("Password", className="text-muted")], className="d-flex align-items-center"),
                                    htm.Div([htm.Span(f"{envs.psqlUser}", className="text-success")], className="fw-semibold")
                                ], className="col-md-6"),
                            ], className="row mb-3"),

                            htm.Div([
                                htm.Div(htm.Small("Immich Root Path", className="text-muted"), className="d-flex align-items-center"),
                                htm.Div(envs.immichPath or htm.Span("(Not configured)", className="text-warning"), className="fw-semibold text-break"),
                            ], className="row mb-3"),

                            htm.Div([
                                htm.Div(htm.Small("Qdrant URL", className="text-muted"), className="d-flex align-items-center"),
                                htm.Div(envs.qdrantUrl or htm.Span("(Not configured)", className="text-warning"), className="fw-semibold text-break"),
                            ], className="row mb-3"),

                        ])
                    ])
                ], className="border-0 shadow-sm")
            ], className="col-lg-10 mb-4"),


            htm.Div([

                cardSets.renderCard()

            ], className="border-0 shadow-sm")

        ], className="row"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #====== bottom end ======================================================
    ])
