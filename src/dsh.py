import dash

# noinspection PyUnresolvedReferences
import dash_bootstrap_components as dbc
# noinspection PyUnresolvedReferences
from dash import html as htm, dcc
# noinspection PyUnresolvedReferences
from dash.dependencies import Input as inp, Output as out, State as ste
# noinspection PyUnresolvedReferences
from dash.dependencies import ALL, MATCH
# noinspection PyUnresolvedReferences
from dash import callback, no_update as noUpd, callback_context as ctx
# noinspection PyUnresolvedReferences
from dash.exceptions import PreventUpdate as preventUpdate

import diskcache
from dash import DiskcacheManager as dskMgr
import os
from uuid import uuid4

from conf import pathCache, pathFromRoot
from util import log

lg = log.get(__name__)

os.makedirs(pathCache, exist_ok=True)

launch_uid = uuid4()
cache = diskcache.Cache(pathCache)
bgCallbackManager = dskMgr(
    cache,
    cache_by=[lambda: launch_uid],
    expire=3600
)


def getTriggerId(ctx=None):
    ctx = dash.callback_context if ctx is None else ctx

    # lg.info( f"[getTriggerId] tid[{ctx.triggered_id}] propid[{ctx.triggered[0]['prop_id']}] len[{len(ctx.triggered)}]" )

    return ctx.triggered[0]['prop_id'].split('.')[0]


def registerScss():
    import sass
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    def compile_sass():
        lg.info( "compile scss.." )
        sass_dir = pathFromRoot('src/scss')
        css_dir = pathFromRoot('src/assets')
        sass.compile(dirname=(sass_dir, css_dir), output_style='compact')

    class ScssHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.scss'): compile_sass()

    os.makedirs(pathFromRoot('src/assets'), exist_ok=True)
    os.makedirs(pathFromRoot('src/scss'), exist_ok=True)

    compile_sass()

    observer = Observer()
    observer.schedule(ScssHandler(), pathFromRoot('src/scss'), recursive=True)
    observer.start()
