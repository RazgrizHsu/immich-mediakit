from conf import ks, envs
from dsh import dash, htm
from util import log

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.settings}',
    title=f"{ks.title}: " + 'System Settings',
)

#========================================================================
def layout():
    return htm.Div([
        htm.H3("System Settings", className="mb-4"),

        htm.Div([
            htm.Div([
                htm.H5("API Settings", className="mb-3"),

                htm.Div([
                    htm.Strong("Immich Server URL: "),
                    htm.Span(envs.immichUrl or "(Not set)")
                ], className="mb-3"),


            ], className="bg-dark p-3 mb-4 border rounded"),

            htm.Div([
                htm.H5("PostgreSQL Settings", className="mb-3"),

                htm.Div([
                    htm.Strong("Hostname: "),
                    htm.Span(envs.psqlHost or "(Not set)")
                ], className="mb-3"),

                htm.Div([
                    htm.Strong("Port: "),
                    htm.Span(envs.psqlPort or "5432")
                ], className="mb-3"),

                htm.Div([
                    htm.Strong("Database name: "),
                    htm.Span(envs.psqlDb or "(Not set)")
                ], className="mb-3"),

                htm.Div([
                    htm.Strong("Username: "),
                    htm.Span(envs.psqlUser or "(Not set)")
                ], className="mb-3"),

                htm.Div([
                    htm.Strong("Password: "),
                    htm.Span("**********" if envs.psqlPass else "(Not set)")
                ], className="mb-3"),

                htm.Div([
                    htm.Strong("Immich Root Path: "),
                    htm.Span(envs.immichPath or "(Not set)"),
                    htm.Div(htm.Small("Full path to the Immich library, used for direct access to image files"), className="text-muted")
                ], className="mb-3"),

            ], className="bg-dark p-3 mb-4 border rounded"),

            htm.Div([
                htm.H5("Other Settings", className="mb-3"),

                htm.Div([
                    htm.Strong("Qdrant URL: "),
                    htm.Span(envs.qdrantUrl or "(Not set)"),
                    htm.Div(htm.Small("URL for the Qdrant vector database"), className="text-muted")
                ], className="mb-3"),

            ], className="bg-dark p-3 mb-4 border rounded"),

            htm.Div([
                htm.P("Note: All settings must be configured through environment variables or the .env file, and cannot be modified through the UI.", className="text-warning")
            ]),
        ]),
    ])
