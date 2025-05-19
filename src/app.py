import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dsh import dash, htm, dcc, dbc
from dsh import bgCallbackManager
from util import log, notify, session, task, err, modal
from ui import layout
import conf, db, api

db.init()

app = dash.Dash(
    __name__,
    title=conf.Ks.title,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder="pages",
    background_callback_manager=bgCallbackManager,
)

err.injectCallbacks(app)

import serve
serve.regBy(app)
layout.regBy(app)
task.regBy(app)
notify.regBy(app)
modal.regBy(app)

import pages
pages.regBy(app)

#========================================================================
app.layout = htm.Div([

    session.render(),

    dcc.Location(id='url', refresh=False),

    layout.renderHeader(),

    dbc.Container([
        dbc.Row([
            dbc.Col([layout.renderSideBar()], width=3, className="sidebar-column"),
            dbc.Col([

                htm.Div(notify.render()),
                htm.Div(modal.render()),

                htm.Div(task.render(), className="m-4"),

                htm.Div(dash.page_container, className="m-3"),

            ], width=9, className="content-column")
        ], className="mt-4")
    ], fluid=True, className="pt-4 flex-grow-1"),

    layout.renderFooter(),


], className="d-flex flex-column min-vh-100")

#========================================================================
if __name__ == "__main__":
    lg = log.get(__name__)
    try:
        lg.info("=======================================")
        lg.info("Starting Dash application...")

        if log.log_file: lg.info(f"Log file recording: {log.log_file}")

        lg.info("---------------------------------------")

        app.run_server(
            debug=True,
            host='0.0.0.0',
            port=int(conf.envs.mkitPort),
            dev_tools_ui=False,
            dev_tools_props_check=True,
            dev_tools_hot_reload=True,
            dev_tools_silence_routes_logging=True,
            dev_tools_serve_dev_bundles=True,
        )

    finally:
        import db

        db.close()
        lg.info("---------------------------------------")
        lg.info("Application closed, all connections closed")
        lg.info("=======================================")
