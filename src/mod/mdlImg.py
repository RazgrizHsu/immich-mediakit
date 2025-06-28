from typing import Optional
from dsh import htm, dcc, dbc, inp, out, ste, cbk, ctx, noUpd, getTrgId, ALL
from dsh import ccbk, cbkFn

from conf import ks
from mod import models
from ui import gvEx
from util import log


lg = log.get(__name__)


class k:
    modal = "img-modal"
    store = ks.sto.mdlImg
    content = "img-modal-content"
    floatL = "img-modal-floatL"
    floatR = "img-modal-floatR"

    help = "img-modal-help"
    btnHelp = "btn-img-help"

    info = "img-modal-info"
    btnInfo = "btn-img-info"

    btnMode = "btn-img-mode"
    btnPrev = "btn-img-prev"
    btnNext = "btn-img-next"
    btnSelect = "btn-img-select"
    navCtrls = "img-nav-controls"

    txtHAuto = "🔄 Auto Height"
    txtHFix = "🔄 Fixed Height"

    cssAuto = "auto"


#------------------------------------------------------------------------
# Helper functions
#------------------------------------------------------------------------
def _isAssetSelected(ste, autoId) -> bool:
    if not ste or not ste.selectedIds or not autoId: return False
    return autoId in ste.selectedIds


def _getAssetBy(now, assId) -> Optional[models.Asset]:
    if now.sim.assCur and assId:
        return next((a for a in now.sim.assCur if a.id == assId), None)
    return None


def _getNavStyles(mdl, now):
    if mdl.isMulti and now.sim.assCur and len(now.sim.assCur) > 1:
        prevStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx <= 0 else "1"}
        nextStyle = {"display": "block", "opacity": "0.3" if mdl.curIdx >= len(now.sim.assCur) - 1 else "1"}
    else:
        prevStyle = {"display": "none"}
        nextStyle = {"display": "none"}
    return prevStyle, nextStyle


def _getSelectBtnState(isSelected):
    if isSelected:
        return "✅ Selected", "success"
    return "◻️ Select", "primary"


def _getHelpState(mdl: models.MdlImg):
    css = "help collapsed" if mdl.helpCollapsed else "help"
    txt = "❔" if mdl.helpCollapsed else "❎"
    if not mdl.isMulti: css = "hide"
    return css, txt


def _getInfoState(mdl: models.MdlImg):
    css = "info collapsed" if mdl.infoCollapsed else "info"
    txt = "ℹ️" if mdl.infoCollapsed else "❎"
    if not mdl.isMulti: css = "hide"
    return css, txt




#------------------------------------------------------------------------
# ui
#------------------------------------------------------------------------
layoutHelp = htm.Div([

    htm.Div([
        dbc.Button(
            id=k.btnHelp,
            color="link",
            size="sm",
            className="float-end p-0",
        ),
        htm.Div([
            htm.H6("Keyboard Shortcuts", className="mb-2"),
            htm.Table([
                htm.Tbody([
                    htm.Tr([
                        htm.Td(htm.Code("Space")),
                        htm.Td("Toggle selection", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("← / h")),
                        htm.Td("Previous image", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("→ / l")),
                        htm.Td("Next image", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("i")),
                        htm.Td("Toggle info table", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("m")),
                        htm.Td("Toggle scale mode", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("ESC / q")),
                        htm.Td("Close modal", className="ps-3")
                    ]),
                    htm.Tr([
                        htm.Td(htm.Code("?")),
                        htm.Td("Toggle help", className="ps-3")
                    ]),
                ])
            ], className="small")
        ], className="help-content")
    ], className="desc"),
], id=k.help, className="help")

layoutInfo = htm.Div([
    htm.Div([
        dbc.Button(
            id=k.btnInfo,
            color="link",
            size="sm",
            className="float-end p-0",
        ),
        htm.Div([
            htm.H6("Image Information", className="mb-2"),
            htm.Div(id=f"{k.info}-content")
        ], className="info-content")
    ], className="desc"),
], id=k.info, className="info")


def render():
    return [
        # Dummy element for mdlImg current autoId tracking
        htm.Div(id={"type": "dummy-output", "id": "mdlimg-current"}, style={"display": "none"}),

        dbc.Modal([
            dbc.ModalHeader([
                htm.Span("Image Preview", className="me-auto"),
                dbc.Button(
                    k.txtHFix,
                    id=k.btnMode,
                    color="secondary",
                    size="sm",
                ),
            ], close_button=True),
            dbc.ModalBody([
                htm.Div(id=k.content, className="img"),
                htm.Div([
                    dbc.Button(
                        "📌 Select",
                        id=k.btnSelect,
                        color="info",
                        className="",
                        style={"display": "none"}
                    ),
                ], className="acts"),
                htm.Div([layoutInfo], id=k.floatL, className="acts L"),
                htm.Div(id=k.floatR, className="acts R"),
                layoutHelp,
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

        dcc.Store(id=k.store),
    ]


#------------------------------------------------------------------------
# trigger: single
#------------------------------------------------------------------------
@cbk(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop", "aid": ALL}, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnImgPopClicked(clks, dta_mdl):
    if not clks or not any(clks): return noUpd

    if not ctx.triggered: return noUpd

    mdl = models.MdlImg.fromDic(dta_mdl)

    trigIdx = ctx.triggered_id
    if isinstance(trigIdx, dict) and "aid" in trigIdx:
        aid = trigIdx["aid"]
        lg.info(f"[mdlImg] clicked, aid[{aid}]")

        if aid:
            mdl.open = True
            mdl.isMulti = False
            mdl.imgUrl = f"/api/img/{aid}?q=preview"

    return mdl.toDict()


#------------------------------------------------------------------------
# trigger: multi
#------------------------------------------------------------------------
@cbk(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop-multi", "aid": ALL}, "n_clicks"),
    [
        ste(k.store, "data"),
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call=True
)
def mdlImg_OnImgPopMultiClicked(clks, dta_mdl, dta_now):
    if not clks or not any(clks): return noUpd

    if not ctx.triggered: return noUpd

    mdl = models.MdlImg.fromDic(dta_mdl)
    now = models.Now.fromDic(dta_now)

    trigIdx = ctx.triggered_id

    if isinstance(trigIdx, dict) and "aid" in trigIdx:
        aid = trigIdx["aid"]
        lens = len(now.sim.assCur)
        lg.info(f"[mdlImg] clicked, aid[{aid}] lens[{lens}]")

        if aid and now.sim.assCur:
            mdl.open = True
            mdl.isMulti = True
            mdl.imgUrl = f"/api/img/{aid}?q=preview"
            mdl.curIdx = next((i for i, ass in enumerate(now.sim.assCur) if ass.autoId == aid), 0)

    return mdl.toDict()


#------------------------------------------------------------------------
# Client-side callback for mdlImg content update
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onContentUpdate"),

    [
        out(k.modal, "is_open"),
        out(k.content, "children"),
        out(k.btnPrev, "style"),
        out(k.btnNext, "style"),
        out(k.btnSelect, "style"),
        out(k.btnSelect, "children"),
        out(k.btnSelect, "color"),
        out(k.help, "className"),
        out(k.btnHelp, "children"),
        out(k.info, "className"),
        out(k.btnInfo, "children"),
        out(f"{k.info}-content", "children"),
    ],
    inp(k.store, "data"),
    [
        ste(ks.sto.now, "data"),
        ste(ks.sto.ste, "data"),
    ],
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg navigation
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onNavigation"),

    [
        out(k.store, "data", allow_duplicate=True),
        out(k.content, "children", allow_duplicate=True),
        out(k.btnPrev, "style", allow_duplicate=True),
        out(k.btnNext, "style", allow_duplicate=True),
        out(k.btnSelect, "children", allow_duplicate=True),
        out(k.btnSelect, "color", allow_duplicate=True),
    ],
    [
        inp(k.btnPrev, "n_clicks"),
        inp(k.btnNext, "n_clicks"),
    ],
    [
        ste(ks.sto.now, "data"),
        ste(ks.sto.ste, "data"),
        ste(k.store, "data"),
    ],
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg help toggle
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onHelpToggle"),

    [
        out(k.store, "data", allow_duplicate=True),
        out(k.help, "className", allow_duplicate=True),
        out(k.btnHelp, "children", allow_duplicate=True),
    ],
    inp(k.btnHelp, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg info toggle
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onInfoToggle"),

    [
        out(k.store, "data", allow_duplicate=True),
        out(k.info, "className", allow_duplicate=True),
        out(k.btnInfo, "children", allow_duplicate=True),
    ],
    inp(k.btnInfo, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg mode toggle
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onModeToggle"),

    [
        out(k.modal, "className"),
        out(k.btnMode, "children")
    ],
    inp(k.btnMode, "n_clicks"),
    ste(k.modal, "className"),
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg ste changes
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onSteChanged"),

    [
        out(k.btnSelect, "children", allow_duplicate=True),
        out(k.btnSelect, "color", allow_duplicate=True),
    ],
    inp(ks.sto.ste, "data"),
    [
        ste(ks.sto.now, "data"),
        ste(k.store, "data"),
    ],
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback for mdlImg selection
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onBtnSelectToSte"),

    out(ks.sto.ste, "data", allow_duplicate=True),
    [inp(k.btnSelect, "n_clicks")],
    [ste(ks.sto.now, "data"), ste(k.store, "data")],
    prevent_initial_call=True
)

#------------------------------------------------------------------------
# Client-side callback to set current mdlImg autoId for hotkeys
#------------------------------------------------------------------------
ccbk(
    cbkFn("mdlImg", "onStoreToDummy"),

    out({"type": "dummy-output", "id": "mdlimg-current"}, "children"),
    [inp(k.store, "data"), inp(ks.sto.now, "data")],
    prevent_initial_call=True
)
