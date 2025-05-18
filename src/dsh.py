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
import os
from uuid import uuid4

import conf
from util import log

lg = log.get(__name__)

os.makedirs(conf.pathCache, exist_ok=True)

launch_uid = uuid4()
cache = diskcache.Cache(conf.pathCache)
bgCallbackManager = dskMgr(
    cache,
    cache_by=[lambda: launch_uid],
    expire=3600
)


def getTriggerId():
    ctx = dash.callback_context

    #lg.info( f"[getTriggerId] tid[{ctx.triggered_id}] propid[{ctx.triggered[0]['prop_id']}] len[{len(ctx.triggered)}]" )

    return ctx.triggered[0]['prop_id'].split('.')[0]
