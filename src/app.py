import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dsh import dash, htm, dcc, dbc
from util import log, err
from conf import ks
from mod import notify, mdlImg, session, mdl
from mod.mgr import tskSvc
import conf, db

lg = log.get(__name__)


#------------------------------------
# init
#------------------------------------
db.init()

#------------------------------------
app = dash.Dash(
    __name__,
    title=conf.ks.title,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"rel": "icon", "type": "image/x-icon", "href": "/assets/favicon.ico"}
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder="pages",
)

#------------------------------------
err.injectCallbacks(app)

import serve
serve.regBy(app)



#========================================================================
import ui
app.layout = htm.Div([

    dcc.Location(id='url', refresh=False),

    # WebSocket connection managed by app.js
    dcc.Store(id=ks.glo.gws),

    notify.render(),
    session.render(),
    *mdl.render(),
    *mdlImg.render(),

    ui.renderHeader(),

    ui.sidebar.layout(),

    htm.Div(dash.page_container, className="page"),
    ui.renderFooter(),

], className="d-flex flex-column min-vh-100")



#========================================================================
if __name__ == "__main__":
    lg = log.get(__name__)
    try:
        from conf import envs
        lg.info("========================================================================")
        lg.info(f"[MediaKit] Start ... ver[{ envs.version }] {'-DEBUG-' if conf.envs.isDev else ''}")
        lg.info("========================================================================")

        if log.EnableLogFile: lg.info(f"Log recording: {log.log_file}")

        if conf.envs.isDev:

            hotReload = bool(os.getenv( 'HotReload', False ))

            if not hotReload: tskSvc.init()
            else:
                if os.getenv('WERKZEUG_RUN_MAIN') == 'true': tskSvc.init()

            import dsh
            dsh.registerScss()
            app.run(
                debug=True,
                host='0.0.0.0',
                port=int(conf.envs.mkitPort),
                dev_tools_ui=False,
                dev_tools_hot_reload=hotReload,
                dev_tools_props_check=False,
                dev_tools_silence_routes_logging=True,
                dev_tools_serve_dev_bundles=True,
            )

        else:

            tskSvc.init()
            app.run(
                debug=False,
                host='0.0.0.0',
                port=int(conf.envs.mkitPort),
                dev_tools_silence_routes_logging=True,
            )

    finally:
        import db

        db.close()

        import multiprocessing

        multiprocessing.current_process().close()
        lg.info("---------------------------------------")
        lg.info("Application closed, all connections closed")
        lg.info("=======================================")
