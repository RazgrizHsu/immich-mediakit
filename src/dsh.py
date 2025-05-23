import os
import dash

# noinspection PyUnresolvedReferences
import dash_bootstrap_components as dbc
# noinspection PyUnresolvedReferences
from dash import html as htm, dcc
# noinspection PyUnresolvedReferences
from dash import callback, no_update as noUpd, callback_context as ctx
# noinspection PyUnresolvedReferences
from dash.dependencies import ALL, MATCH
# noinspection PyUnresolvedReferences
from dash.dependencies import Input as inp, Output as out, State as ste
# noinspection PyUnresolvedReferences
from dash.exceptions import PreventUpdate as preventUpdate

from conf import pathCache, pathFromRoot
from util import log

lg = log.get(__name__)

os.makedirs(pathCache, exist_ok=True)


def getTriggerId(ctx=None):
    ctx = dash.callback_context if ctx is None else ctx
    return ctx.triggered[0]['prop_id'].split('.')[0]


def registerScss():
    import sass
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    def build():
        sass_dir = pathFromRoot('src/scss')
        css_dir = pathFromRoot('src/assets')
        try:
            sass.compile(dirname=(sass_dir, css_dir), output_style='compact')
        except Exception as e:
            lg.error(f"[scss] compile error: {e}")

    class ScssHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.scss'):
                build()
                lg.info(f"[scss] build: {event.src_path}")

    os.makedirs(pathFromRoot('src/assets'), exist_ok=True)
    os.makedirs(pathFromRoot('src/scss'), exist_ok=True)

    build()

    observer = Observer()
    observer.schedule(ScssHandler(), pathFromRoot('src/scss'), recursive=True)
    observer.start()
