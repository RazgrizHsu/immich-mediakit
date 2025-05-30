import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dsh import dash, htm, dcc, dbc
from dash_extensions import WebSocket
from util import log, err
from mod import notify, modalImg, session, modal, tsk
from mod.mgr import tskSvc
import conf, db

lg = log.get(__name__)

db.init()

tskSvc.init()

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
)

err.injectCallbacks(app)

import serve

serve.regBy(app)

from dsh import callback, inp, out

@callback(
    out("url", "pathname"),
    [
        inp(tsk.k.wsId, "state"),
        inp(tsk.k.wsId, "error")
    ],
    prevent_initial_call=True
)
def monitor_ws_connection(state, error):
    if error:
        lg.error(f"[app:ws] ERROR: {error}")
    elif state:
        # lg.info(f"[app:ws] state changed: {state}")
        pass

    return dash.no_update

import ui
#========================================================================
app.layout = htm.Div([

    dcc.Location(id='url', refresh=False),

    # Global WebSocket connection for task updates
    WebSocket(id=tsk.k.wsId, url=conf.getWebSocketUrl()),

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
