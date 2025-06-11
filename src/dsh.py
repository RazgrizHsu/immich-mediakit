import os
import dash

import dash_bootstrap_components as dbc
from dash import html as htm, dcc
from dash import callback_context as ctx, callback as cbk, clientside_callback as ccbk
from dash import Patch
from dash.dependencies import ALL, MATCH
from dash.dependencies import Input as inp, Output as out, State as ste
from dash.exceptions import PreventUpdate as preventUpdate
from dash import ClientsideFunction as cbkFn


from conf import pathCache, pathFromRoot
from util import log

lg = log.get(__name__)

os.makedirs(pathCache, exist_ok=True)


def getTrgId(ctx=None):
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


class NoUpdList(list):
    """
    Extended no_update array with partial position updates support

    Usage Examples:
    # Create array with 4 no_update values
    noUpd.by(4)  # [no_update, no_update, no_update, no_update]

    # Update single position
    noUpd.by(4).updFr(0, "new_value")  # ["new_value", no_update, no_update, no_update]

    # Update multiple positions (sequential placement from specified index)
    noUpd.by(4).updFr(1, ["val1", "val2"])  # [no_update, "val1", "val2", no_update]

    # Chaining multiple updates
    noUpd.by(4).updFr(0, "first").updFr(2, "third")  # ["first", no_update, "third", no_update]

    # Auto-convert BaseDictModel
    noUpd.by(4).updFr(0, some_model)  # Automatically calls some_model.toDict()

    # Real callback usage example:
    @cbk([
        out("store1", "data"),  # index 0
        out("store2", "data"),  # index 1
        out("store3", "data"),  # index 2
        out("store4", "data"),  # index 3
    ])
    def callback():
        # Only update store1 and store3
        return noUpd.by(4).updFr(0, store1_data).updFr(2, store3_data)

        # Or update multiple at once
        return noUpd.by(4).updFr(0, [store1_data, store2_data])
    """

    def updFr(self, idx, vals):
        """
        Update values sequentially from specified index position

        Args:
            idx: Starting index position
            vals: Values to update - can be single value or array
                 If array, values will be placed sequentially starting from idx

        Examples:
            # Single value at index 1
            noUpd.by(4).updFr(1, "val")  # [no_update, "val", no_update, no_update]

            # Multiple values from index 1
            noUpd.by(4).updFr(1, ["a", "b"])  # [no_update, "a", "b", no_update]

            # Chain updates
            noUpd.by(4).updFr(0, "first").updFr(3, "last")  # ["first", no_update, no_update, "last"]

        Returns:
            New NoUpdList instance
        """
        result = self.copy()
        if not isinstance(vals, list): vals = [vals]
        for i, v in enumerate(vals):
            # Auto-convert BaseDictModel to dict
            from mod.bse.baseModel import BaseDictModel
            if isinstance(v, BaseDictModel): v = v.toDict()
            if idx + i < len(result): result[idx + i] = v
        return result


# noinspection PyProtectedMember
class NoUpdHelper(dash._callback.NoUpdate):
    """
    Extended no_update utility class

    Usage Examples:
    # Create no_update array with specified length
    noUpd.by(3)  # [no_update, no_update, no_update]

    # Use with updFr method
    return noUpd.by(4).updFr(0, data1).updFr(2, data2)
    """

    @classmethod
    def by(cls, count: int):
        """
        Create NoUpdList with specified length

        Args:
            count: Array length

        Returns:
            NoUpdList containing count number of dash.no_update values
        """
        return NoUpdList([dash.no_update for i in range(count)])


noUpd = NoUpdHelper()
