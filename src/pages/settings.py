from conf import ks, envs
from dsh import dash, htm, dbc
from util import log

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.settings}',
    title=f"{ks.title}: " + 'System Settings',
)

#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        dbc.Row([
            dbc.Col(htm.H3(f"{ks.pg.settings.name}"), width=3),
            dbc.Col(htm.Small(f"{ks.pg.settings.desc}", className="text-muted text-right"))
        ], className="mb-4"),

        htm.Div([
            htm.Div([
                dbc.Card([
                    dbc.CardHeader([
                        htm.I(className="bi bi-database-fill me-2", style={"fontSize": "1.2rem"}),
                        "PostgreSQL Configuration"
                    ]),
                    dbc.CardBody([

                        htm.Div([
                            htm.Div([
                                htm.Div([
                                    htm.I(className="bi bi-hdd-network me-2 text-muted"),
                                    htm.Small("Hostname", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div(envs.psqlHost or htm.Span("(Not configured)", className="text-warning"),
                                       className="fw-semibold", style={"fontSize": "1.1rem"})
                            ], className="mb-3"),

                            htm.Div([
                                htm.Div([
                                    htm.Div([
                                        htm.I(className="bi bi-plug me-2 text-muted"),
                                        htm.Small("Port", className="text-muted")
                                    ], className="d-flex align-items-center"),
                                    htm.Div(envs.psqlPort or "5432",
                                           className="fw-semibold", style={"fontSize": "1.1rem"})
                                ], className="col-md-6"),

                                htm.Div([
                                    htm.Div([
                                        htm.I(className="bi bi-archive me-2 text-muted"),
                                        htm.Small("Database", className="text-muted")
                                    ], className="d-flex align-items-center"),
                                    htm.Div(envs.psqlDb or htm.Span("(Not configured)", className="text-warning"),
                                           className="fw-semibold", style={"fontSize": "1.1rem"})
                                ], className="col-md-6"),
                            ], className="row mb-3"),

                            htm.Div([
                                htm.Div([
                                    htm.Div([
                                        htm.I(className="bi bi-person-fill me-2 text-muted"),
                                        htm.Small("Username", className="text-muted")
                                    ], className="d-flex align-items-center"),
                                    htm.Div(envs.psqlUser or htm.Span("(Not configured)", className="text-warning"),
                                           className="fw-semibold", style={"fontSize": "1.1rem"})
                                ], className="col-md-6"),

                                htm.Div([
                                    htm.Div([
                                        htm.I(className="bi bi-key-fill me-2 text-muted"),
                                        htm.Small("Password", className="text-muted")
                                    ], className="d-flex align-items-center"),
                                    htm.Div([
                                        htm.Span("••••••••", className="text-success") if envs.psqlPass
                                        else htm.Span("(Not configured)", className="text-warning"),
                                        htm.I(className="bi bi-shield-check ms-2 text-success" if envs.psqlPass else "")
                                    ], className="fw-semibold", style={"fontSize": "1.1rem"})
                                ], className="col-md-6"),
                            ], className="row mb-3"),

                            htm.Hr(className="my-3", style={"opacity": "0.1"}),

                            htm.Div([
                                htm.Div([
                                    htm.I(className="bi bi-folder-fill me-2 text-muted"),
                                    htm.Small("Immich Root Path", className="text-muted")
                                ], className="d-flex align-items-center"),
                                htm.Div(envs.immichPath or htm.Span("(Not configured)", className="text-warning"),
                                       className="fw-semibold text-break", style={"fontSize": "0.95rem"}),
                                htm.Small("Full path to the Immich library for direct image access",
                                         className="text-muted mt-1 d-block", style={"fontSize": "0.8rem"})
                            ], className=""),
                        ])
                    ])
                ], className="border-0 shadow-sm", style={
                    "borderLeft": "4px solid var(--info-bs)"
                })
            ], className="col-lg-6 mb-4"),

            htm.Div([
                dbc.Card([
                    dbc.CardHeader([
                        htm.I(className="bi bi-diagram-3-fill me-2", style={"fontSize": "1.2rem"}),
                        "Vector Database"
                    ]),
                    dbc.CardBody([

                        htm.Div([
                            htm.Div([
                                htm.I(className="bi bi-link-45deg me-2 text-muted"),
                                htm.Small("Qdrant URL", className="text-muted")
                            ], className="d-flex align-items-center"),
                            htm.Div(envs.qdrantUrl or htm.Span("(Not configured)", className="text-warning"),
                                   className="fw-semibold text-break", style={"fontSize": "1.1rem"}),
                            htm.Small("URL for the Qdrant vector database service",
                                     className="text-muted mt-1 d-block", style={"fontSize": "0.8rem"})
                        ], className="mb-3"),

                        htm.Div([
                            htm.Div([
                                htm.Span([
                                    htm.I(className="bi bi-check-circle-fill me-1 text-success" if envs.qdrantUrl else "bi bi-x-circle-fill me-1 text-danger"),
                                    "Connected" if envs.qdrantUrl else "Not Connected"
                                ], className="badge bg-info px-3 py-2", style={"fontSize": "0.85rem"})
                            ], className="text-center mt-4")
                        ])
                    ])
                ], className="border-0 shadow-sm", style={
                    "borderLeft": "4px solid var(--succ-bs)"
                })
            ], className="col-lg-6 mb-4"),

            htm.Div([
                htm.Div([
                    htm.Div([
                        htm.I(className="bi bi-info-circle-fill me-2", style={"color": "var(--warn-bs)"}),
                        htm.Strong("Configuration Notice")
                    ], className="d-flex align-items-center mb-2"),
                    htm.P([
                        "All settings are managed through environment variables or the ",
                        htm.Code(".env", className="px-2 py-1 bg-dark rounded"),
                        " file. Changes require application restart to take effect."
                    ], className="mb-0", style={"fontSize": "0.9rem"})
                ], className="alert alert-warning border-0 shadow-sm", style={
                    "backgroundColor": "rgba(254, 178, 4, 0.1)",
                    "borderLeft": "4px solid var(--warn-bs)"
                })
            ], className="col-12"),

            htm.Div([
                dbc.Card([
                    dbc.CardHeader([
                        htm.I(className="bi bi-server me-2"),
                        "System Status"
                    ]),
                    dbc.CardBody([
                        htm.Div([
                            htm.Small("Database Connection", className="text-muted"),
                            htm.Div([
                                htm.I(className="bi bi-circle-fill me-2",
                                     style={"fontSize": "0.6rem", "color": "var(--succ-bs)" if envs.psqlHost and envs.psqlDb else "var(--dang-bs)"}),
                                htm.Span("Active" if envs.psqlHost and envs.psqlDb else "Inactive",
                                        className="text-success" if envs.psqlHost and envs.psqlDb else "text-danger")
                            ])
                        ], className="d-flex justify-content-between align-items-center py-2 border-bottom"),

                        htm.Div([
                            htm.Small("Vector Service", className="text-muted"),
                            htm.Div([
                                htm.I(className="bi bi-circle-fill me-2",
                                     style={"fontSize": "0.6rem", "color": "var(--succ-bs)" if envs.qdrantUrl else "var(--dang-bs)"}),
                                htm.Span("Active" if envs.qdrantUrl else "Inactive",
                                        className="text-success" if envs.qdrantUrl else "text-danger")
                            ])
                        ], className="d-flex justify-content-between align-items-center py-2 border-bottom"),

                        htm.Div([
                            htm.Small("Image Library", className="text-muted"),
                            htm.Div([
                                htm.I(className="bi bi-circle-fill me-2",
                                     style={"fontSize": "0.6rem", "color": "var(--succ-bs)" if envs.immichPath else "var(--warn-bs)"}),
                                htm.Span("Configured" if envs.immichPath else "Not Set",
                                        className="text-success" if envs.immichPath else "text-warning")
                            ])
                        ], className="d-flex justify-content-between align-items-center py-2"),
                    ])
                ])
            ], className="border-0 shadow-sm")

        ], className="row"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #====== bottom end ======================================================
    ])
