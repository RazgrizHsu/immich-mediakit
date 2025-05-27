from dsh import dash, htm, dcc, dbc, inp, out, ste, callback, noUpd, getTriggerId
from util import log
from conf import ks

from mod import models

lg = log.get(__name__)


class k:
    modal = "img-modal"
    store = ks.sto.mdlImg
    modalContent = "img-modal-content"
    btnModeChg = "btn-img-mode-chg"

    txtHAuto = "🔄 Auto Height"
    txtHFix = "🔄 Fixed Height"
    clsAuto = "auto"

def render():
    return [
        dbc.Modal([
            dbc.ModalHeader([
                htm.Span("Image Preview", className="me-auto"),
                dbc.Button(
                    k.txtHFix,
                    id=k.btnModeChg,
                    color="secondary",
                    size="sm",
                ),
            ], close_button=True),
            dbc.ModalBody(
                htm.Div(id=k.modalContent)
            ),
        ],
            id=k.modal,
            size="xl",
            centered=True,
            fullscreen=True,
            className="img-pop",
        ),

        # Store for clicked image ID
        dcc.Store(id=k.store, data=None)
    ]

#------------------------------------------------------------------------
# Image Preview Modal Callback
#------------------------------------------------------------------------
@callback(
    [
        out(k.modal, "is_open"),
        out(k.modalContent, "children"),
    ],
    inp(k.store, "data"),
    ste(k.modal, "is_open"),
    prevent_initial_call=True
)
def mdlImg_IsOpen(dta_mdl, is_open):
    ctx = dash.callback_context
    if not ctx.triggered: return noUpd, noUpd

    trigger_id = getTriggerId()

    lg.info(f"[mdlImg] dta_mdl: {dta_mdl}")

    if trigger_id != k.store: return noUpd, noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    htms = []

    if mdl.imgUrl:
        htms.append(htm.Img(src=mdl.imgUrl))

    return mdl.open, htms


@callback(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop", "index": dash.ALL}, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnImgPopClicked(clks, dta_mdl):
    if not clks or not any(clks): return noUpd

    ctx = dash.callback_context
    if not ctx.triggered: return noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    trigIdx = ctx.triggered_id
    if isinstance(trigIdx, dict) and "index" in trigIdx:
        assId = trigIdx["index"]
        lg.info(f"[mdlImg] clicked, assId[{assId}] clicked[{clks}]")

        if assId:
            mdl.open = True
            mdl.imgUrl = f"/api/img/{assId}?q=preview"

    return mdl.toDict()


@callback(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop-multi", "index": dash.ALL}, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnImgPopMultiClicked(clks, dta_mdl):
    if not clks or not any(clks): return noUpd

    ctx = dash.callback_context
    if not ctx.triggered: return noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    idxs = []
    for i, inp in enumerate(ctx.inputs_list[0]):
        if 'index' in inp['id']:
            idxs.append(inp['id']['index'])

    lg.info(f"[mdlImg] all indexes: {idxs}")

    trigIdx = ctx.triggered_id
    if isinstance(trigIdx, dict) and "index" in trigIdx:
        assId = trigIdx["index"]
        lg.info(f"[mdlImg] clicked, assId[{assId}] clicked[{clks}]")

        if assId:
            mdl.open = True
            mdl.imgUrl = f"/api/img/{assId}?q=preview"

    return mdl.toDict()


@callback(
    [
        out(k.modal, "className"),
        out(k.btnModeChg, "children")
    ],
    inp(k.btnModeChg, "n_clicks"),
    ste(k.modal, "className"),
    prevent_initial_call=True
)
def mdlImg_toggleMode(n_clicks, classes):
    if not n_clicks: return [noUpd, noUpd]

    if not classes: classes = ""

    hasClass = k.clsAuto in classes.split()

    if hasClass:
        css = " ".join([c for c in classes.split() if c != k.clsAuto])
        txt = k.txtHFix
    else:
        css = classes + f" {k.clsAuto}" if classes else k.clsAuto
        txt = k.txtHAuto

    return [css, txt]
