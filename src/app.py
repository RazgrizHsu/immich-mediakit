import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dsh import dash, htm, dcc, dbc
from dsh import bgCallbackManager
from util import log, notify, session, task, err, modal, modalImg
from ui import layout
import conf, db

db.init()

app = dash.Dash(
    __name__,
    title=conf.ks.title,
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
modalImg.regBy(app)

import pages
pages.regBy(app)

#========================================================================
app.layout = htm.Div([

    session.render(),
    *modal.render(),
    *modalImg.render(),

    dcc.Location(id='url', refresh=False),

    layout.renderHeader(),

    dbc.Container([
        dbc.Row([
            dbc.Col([layout.renderSideBar()], width=3, className="L"),
            dbc.Col([

                htm.Div(notify.render()),

                htm.Div(task.render(), className="m-4"),

                htm.Div(dash.page_container),

            ], width=9, className="R")
        ], className="mt-4")
    ], fluid=True, className="pt-4 flex-grow-1"),

    layout.renderFooter(),


], className="d-flex flex-column min-vh-100 layout")

#========================================================================
if __name__ == "__main__":
    lg = log.get(__name__)
    try:
        lg.info("=======================================")
        lg.info(f"Starting Dash {'-DEBUG-'if conf.envs.isDev else ''}")

        if log.EnableLogFile: lg.info(f"Log file recording: {log.log_file}")

        lg.info("---------------------------------------")
        if conf.envs.isDev:
            import dsh
            dsh.registerScss()
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
        else:
            app.run_server(
                debug=False,
                host='0.0.0.0',
                port=int(conf.envs.mkitPort),
            )


    finally:
        import db
        db.close()

        import multiprocessing
        multiprocessing.current_process().close()
        lg.info("---------------------------------------")
        lg.info("Application closed, all connections closed")
        lg.info("=======================================")
