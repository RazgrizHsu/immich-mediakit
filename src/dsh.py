import dash

# noinspection PyUnresolvedReferences
import dash_bootstrap_components as dbc
# noinspection PyUnresolvedReferences
from dash import html as htm, dcc
# noinspection PyUnresolvedReferences
from dash.dependencies import Input as inp, Output as out, State as ste, ALL
# noinspection PyUnresolvedReferences
from dash import callback, no_update as noUpd, callback_context as ctx
# noinspection PyUnresolvedReferences
from dash.exceptions import PreventUpdate as preventUpdate

import diskcache
from dash import DiskcacheManager as dskMgr

import conf

cache = diskcache.Cache( conf.pathCache )
bgCallbackManager = dskMgr(cache)


def getTriggerId():
    ctx = dash.callback_context
    return ctx.triggered[0]['prop_id'].split('.')[0]
