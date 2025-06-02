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
    btnPrev = "btn-img-prev"
    btnNext = "btn-img-next"
    btnSelect = "btn-img-select"
    navCtrls = "img-nav-controls"
    autoIdBadge = "img-autoid-badge"

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
            dbc.ModalBody([
                htm.Div(id=k.modalContent),
                htm.Div([
                    htm.Span(
                        "",
                        id=k.autoIdBadge,
                        className="tag lg",
                        style={"display": "none"}
                    ),
                    dbc.Button(
                        "📌 Select",
                        id="btn-img-select",
                        color="info",
                        className="",
                        style={"display": "none"}
                    ),
                ], className="acts"),
                dbc.Button(
                    "←",
                    id=k.btnPrev,
                    color="secondary",
                    size="lg",
                    className="position-fixed start-0 top-50 translate-middle-y ms-3",
                    style={"zIndex": 1000, "display": "none"}
                ),
                dbc.Button(
                    "→",
                    id=k.btnNext,
                    color="secondary",
                    size="lg",
                    className="position-fixed end-0 top-50 translate-middle-y me-3",
                    style={"zIndex": 1000, "display": "none"}
                ),
            ]),
        ],
            id=k.modal,
            size="xl",
            centered=True,
            fullscreen=True,
            className="img-pop",
        ),

        # Store for clicked image ID
        dcc.Store(id=k.store, data=None),
    ]

#------------------------------------------------------------------------
# Image Preview Modal Callback
#------------------------------------------------------------------------
@callback(
    [
        out(k.modal, "is_open"),
        out(k.modalContent, "children"),
        out(k.btnPrev, "style"),
        out(k.btnNext, "style"),
        out(k.autoIdBadge, "style"),
        out(k.autoIdBadge, "children"),
        out(k.btnSelect, "style"),
        out(k.btnSelect, "children"),
        out(k.btnSelect, "color"),
    ],
    inp(k.store, "data"),
    ste(k.modal, "is_open"),
    prevent_initial_call=True
)
def mdlImg_IsOpen(dta_mdl, is_open):
    ctx = dash.callback_context
    if not ctx.triggered: return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    trigger_id = getTriggerId()

    # lg.info(f"[mdlImg] dta_mdl: {dta_mdl}")

    if trigger_id != k.store: return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    htms = []

    if mdl.imgUrl:
        htms.append(htm.Img(src=mdl.imgUrl))

    prevStyle = {"display": "none"}
    nextStyle = {"display": "none"}

    if mdl.isMulti and len(mdl.args) > 1:
        prevStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx <= 0 else "1"}
        nextStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx >= len(mdl.args) - 1 else "1"}

    badgeStyle = {"display": "block"} if mdl.isMulti else {"display": "none"}
    badgeText = ""
    btnSelectStyle = {"display": "none"}
    btnSelectText = "◻️ Select"
    btnSelectColor = "primary"

    if mdl.isMulti and mdl.args and mdl.curIdx < len(mdl.args):
        curAss = mdl.args[mdl.curIdx]
        badgeText = f"#{curAss.get('autoId', '')}"
        btnSelectStyle = {"display": "block"}
        if curAss.get('selected', False):
            btnSelectText = "✅ Selected"
            btnSelectColor = "success"

    return mdl.open, htms, prevStyle, nextStyle, badgeStyle, badgeText, btnSelectStyle, btnSelectText, btnSelectColor


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
            mdl.isMulti = False
            mdl.open = True
            mdl.imgUrl = f"/api/img/{assId}?q=preview"

    return mdl.toDict()


@callback(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop-multi", "id": dash.ALL, "autoId": dash.ALL, "selected": dash.ALL}, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnImgPopMultiClicked(clks, dta_mdl):
    if not clks or not any(clks): return noUpd

    ctx = dash.callback_context

    if not ctx.triggered: return noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    mdl.args = []
    for i, inp in enumerate(ctx.inputs_list[0]):
        if 'id' in inp['id'] and 'autoId' in inp['id']:
            obj = {'id': inp['id']['id'], 'autoId': inp['id']['autoId'], 'selected': inp['id'].get('selected', False)}
            mdl.args.append(obj)

    lg.info(f"[mdlImg] mdl.args: {mdl.args}")

    trigIdx = ctx.triggered_id
    if isinstance(trigIdx, dict) and "id" in trigIdx:
        assId = trigIdx["id"]
        lg.info(f"[mdlImg] clicked, assId[{assId}] clicked[{clks}]")

        if assId:
            mdl.open = True
            mdl.imgUrl = f"/api/img/{assId}?q=preview"
            mdl.isMulti = True
            mdl.curIdx = next((i for i, arg in enumerate(mdl.args) if arg['id'] == assId), 0)

    return mdl.toDict()


@callback(
    [
        out(k.store, "data", allow_duplicate=True),
        out(k.autoIdBadge, "children", allow_duplicate=True),
        out(k.btnPrev, "style", allow_duplicate=True),
        out(k.btnNext, "style", allow_duplicate=True),
        out(k.btnSelect, "children", allow_duplicate=True),
        out(k.btnSelect, "color", allow_duplicate=True),
    ],
    [
        inp(k.btnPrev, "n_clicks"),
        inp(k.btnNext, "n_clicks"),
    ],
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnNavClicked(prev_clicks, next_clicks, dta_mdl):
    if not prev_clicks and not next_clicks: return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    ctx = dash.callback_context
    if not ctx.triggered: return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    mdl = models.MdlImg.fromDict(dta_mdl)

    if not mdl.isMulti or not mdl.args: return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    trigger_id = getTriggerId()

    if trigger_id == k.btnPrev:
        if mdl.curIdx > 0:
            mdl.curIdx = mdl.curIdx - 1
        else:
            return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd
    elif trigger_id == k.btnNext:
        if mdl.curIdx < len(mdl.args) - 1:
            mdl.curIdx = mdl.curIdx + 1
        else:
            return noUpd, noUpd, noUpd, noUpd, noUpd, noUpd

    curAss = mdl.args[mdl.curIdx]
    mdl.imgUrl = f"/api/img/{curAss['id']}?q=preview"

    badgeText = f"#{curAss.get('autoId', '')}"

    prevStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx <= 0 else "1"}
    nextStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx >= len(mdl.args) - 1 else "1"}

    btnSelectText = "✅ Selected" if curAss.get('selected', False) else "📌 Select"
    btnSelectColor = "success" if curAss.get('selected', False) else "primary"

    lg.info(f"[mdlImg] nav to idx[{mdl.curIdx}] assId[{curAss['id']}] autoId[{curAss.get('autoId', '')} selected[{curAss.get('selected', False)}]")

    return mdl.toDict(), badgeText, prevStyle, nextStyle, btnSelectText, btnSelectColor


@callback(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
        out(k.store, "data", allow_duplicate=True),
        out(k.btnSelect, "children", allow_duplicate=True),
        out(k.btnSelect, "color", allow_duplicate=True),
    ],
    inp(k.btnSelect, "n_clicks"),
    [
        ste(ks.sto.now, "data"),
        ste(k.store, "data"),
    ],
    prevent_initial_call=True
)
def mdlImg_OnSelectClicked(n_clicks, dta_now, dta_mdl):
    if not n_clicks: return noUpd, noUpd, noUpd, noUpd

    now = models.Now.fromDict(dta_now)
    mdl = models.MdlImg.fromDict(dta_mdl)

    if not mdl.isMulti or not mdl.args or mdl.curIdx >= len(mdl.args):
        return noUpd, noUpd, noUpd, noUpd

    curAss = mdl.args[mdl.curIdx]
    assId = curAss.get('id')

    if not assId or not now.pg.sim.assCur:
        return noUpd, noUpd, noUpd, noUpd

    for ass in now.pg.sim.assCur:
        if ass.id == assId:
            ass.selected = not ass.selected
            lg.info(f'[mdlImg:select] toggled: {ass.autoId}, selected: {ass.selected}')
            mdl.args[mdl.curIdx]['selected'] = ass.selected
            break

    selected = [ass for ass in now.pg.sim.assCur if ass.selected]
    now.pg.sim.assSelect = selected

    btnText = "✅ Selected" if curAss.get('selected', False) else "◻️ Select"
    btnColor = "success" if curAss.get('selected', False) else "primary"

    return now.toDict(), mdl.toDict(), btnText, btnColor


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
