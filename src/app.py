import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dsh import dash, htm, dcc, dbc, bgMgr
from util import log, session, err, modal, modalImg, notify
import conf, db, ui

db.init()

app = dash.Dash(
    __name__,
    title=conf.ks.title,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"rel": "icon", "type": "image/x-icon", "href": "/assets/favicon.ico"}
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder="pages",
    background_callback_manager=bgMgr,
)

err.injectCallbacks(app)

import serve, pages, util

serve.regBy(app)

import ui
#========================================================================
app.layout = htm.Div([

    dcc.Location(id='url', refresh=False),

    notify.render(),
    session.render(),
    *modal.render(),
    *modalImg.render(),

    ui.renderHeader(),

    ui.sidebar.layout(),

    htm.Div(dash.page_container, className="page"),
    ui.renderFooter(),

], className="d-flex flex-column min-vh-100")



#========================================================================
if __name__ == "__main__":
    lg = log.get(__name__)
    try:
        lg.info("=======================================")
        lg.info(f"Starting Dash {'-DEBUG-' if conf.envs.isDev else ''}")

        if log.EnableLogFile: lg.info(f"Log file recording: {log.log_file}")

        lg.info("---------------------------------------")
        if conf.envs.isDev:
            import dsh

            dsh.registerScss()
            app.run(
                debug=True,
                host='0.0.0.0',
                port=int(conf.envs.mkitPort),
                dev_tools_ui=False,
                dev_tools_hot_reload=True,
                dev_tools_props_check=False,
                dev_tools_silence_routes_logging=True,
                dev_tools_serve_dev_bundles=True,
            )
        else:
            app.run(
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
