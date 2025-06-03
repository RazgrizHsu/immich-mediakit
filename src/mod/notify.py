from dsh import dash, htm, dbc, out, inp, ste, cbk, ALL
from util import log
from mod import models
from conf import ks

lg = log.get(__name__)

class k:
    succ = 'success'
    erro = 'error'
    warn = 'warning'
    info = 'info'

    divId = 'div-notify'


def render():
    return htm.Div([
        htm.Div(
            id=k.divId,
            style={
                'position': 'fixed',
                'top': '58px',
                'left': '38px',
                'maxWidth': '500px',
                'zIndex': '1000'
            },
            className="notify"
        )
    ])

@cbk(
    out(k.divId, 'children'),
    inp(ks.sto.nfy, 'data')
)
def update_notifications(dta_nfy):
    if not dta_nfy: return []

    nfy = models.Nfy.fromDict(dta_nfy)

    divs = []

    msgs = list(nfy.msgs.items())
    msgs.reverse()

    for nid, data in msgs:
        msg = data['message']

        # lg.info(f"[notify] Update notification: {data['message']}")
        divs.append(
            dbc.Alert(
                msg, 
                id={'type': 'notify-alert', 'index': nid},
                color=data['type'],
                dismissable=True,
                duration=data['timeout'],
                is_open=True,
                fade=True,
                className="mb-2 mt-2 glow-light"
            )
        )

    # lg.info( f"[notify] Update notifications, total[{len(divs)}]" )
    return divs

@cbk(
    out(ks.sto.nfy, 'data', allow_duplicate=True),
    inp({'type': 'notify-alert', 'index': ALL}, 'is_open'),
    ste({'type': 'notify-alert', 'index': ALL}, 'id'),
    ste(ks.sto.nfy, 'data'),
    prevent_initial_call=True
)
def remove_notification(itemOpened, itemIds, dta_nfy):
    if not dta_nfy: return dash.no_update
    if not any(itemIds) or all(itemOpened): return dash.no_update

    nfy = models.Nfy.fromDict(dta_nfy)

    # Find the IDs of closed
    cIds = []
    for i, is_open in enumerate(itemOpened):
        if not is_open and i < len(itemIds):
            cIds.append(itemIds[i]['index'])

    if not cIds: return dash.no_update

    # remove closed
    newMsgs = {k: v for k, v in nfy.msgs.items() if k not in cIds}

    nfy.msgs = newMsgs

    return nfy.toDict()
