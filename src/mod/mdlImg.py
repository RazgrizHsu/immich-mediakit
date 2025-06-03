from dsh import htm, dcc, dbc, inp, out, ste, cbk, ctx, noUpd, getTrgId, ALL
from util import log
from conf import ks, co

from mod import models

lg = log.get(__name__)


class k:
    modal = "img-modal"
    store = ks.sto.mdlImg
    content = "img-modal-content"
    floatL = "img-modal-floatL"
    floatR = "img-modal-floatR"

    help = "img-modal-help"
    btnHelp = "btn-img-help"

    btnMode = "btn-img-mode"
    btnPrev = "btn-img-prev"
    btnNext = "btn-img-next"
    btnSelect = "btn-img-select"
    navCtrls = "img-nav-controls"
    showIds = "img-autoid-badge"

    txtHAuto = "🔄 Auto Height"
    txtHFix = "🔄 Fixed Height"

    cssAuto = "auto"

#------------------------------------------------------------------------
# Helper functions
#------------------------------------------------------------------------
def _getAssetBy(now, assId):
    if now.sim.assCur and assId:
        return next((a for a in now.sim.assCur if a.id == assId), None)
    return None

def _buildAssetInfo(ass):
    if not ass: return []
    return [
        htm.Span(f"Size: {co.fmt.size(ass.jsonExif.fileSizeInByte) if ass.jsonExif else 'N/A'}",
                 className="badge bg-info me-2"),
        htm.Span(f"File: {ass.originalFileName}", className="badge bg-secondary"),
    ]

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

def _getHelpState(helpCollapsed):
    helpClass = "help collapsed" if helpCollapsed else "help"
    helpBtnText = "❔" if helpCollapsed else "❎"
    return helpClass, helpBtnText

def _buildImageContent(mdl, now):
    htms = []
    badgeText = ""

    if mdl.imgUrl:
        htms.append(htm.Img(src=mdl.imgUrl))

    if mdl.isMulti and now.sim.assCur and mdl.curIdx < len(now.sim.assCur):
        fullAss = now.sim.assCur[mdl.curIdx]

        if fullAss:
            badgeText = f"#{fullAss.autoId} @{fullAss.simGID}"
            htms.append(htm.Div(_buildAssetInfo(fullAss), className="mt-2"))

    return htms, badgeText


#------------------------------------------------------------------------
# ui
#------------------------------------------------------------------------
def render():
    return [
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
                htm.Div(id=k.content),
                htm.Div([
                    htm.Span(
                        id=k.showIds,
                        className="tag lg",
                        style={"display": "none"}
                    ),
                    dbc.Button(
                        "📌 Select",
                        id=k.btnSelect,
                        color="info",
                        className="",
                        style={"display": "none"}
                    ),
                ], className="acts"),
                htm.Div(id=k.floatL, className="acts L"),
                htm.Div(id=k.floatR, className="acts R"),
                htm.Div([

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
                                        htm.Td(htm.Code("m")),
                                        htm.Td("Toggle Scale Mode", className="ps-3")
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
                ], id=k.help, className="help"),
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
# callbacks
#------------------------------------------------------------------------
@cbk(
    [
        out(k.modal, "is_open"),
        out(k.content, "children"),
        out(k.btnPrev, "style"),
        out(k.btnNext, "style"),
        out(k.showIds, "style"),
        out(k.showIds, "children"),
        out(k.btnSelect, "style"),
        out(k.btnSelect, "children"),
        out(k.btnSelect, "color"),
        out(k.help, "className"),
        out(k.btnHelp, "children"),
    ],
    inp(k.store, "data"),
    [
        ste(k.modal, "is_open"),
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call=True
)
def mdlImg_IsOpen(dta_mdl, is_open, dta_now):
    if not ctx.triggered: return noUpd.by(11)

    trgId = getTrgId()

    # lg.info(f"[mdlImg] dta_mdl: {dta_mdl}")

    if trgId != k.store: return noUpd.by(11)

    mdl = models.MdlImg.fromDict(dta_mdl)
    now = models.Now.fromDict(dta_now)

    htms = []

    htms, badgeText = _buildImageContent(mdl, now)
    prevStyle, nextStyle = _getNavStyles(mdl, now)

    badgeStyle = {"display": "block"} if mdl.isMulti else {"display": "none"}
    btnSelectStyle = {"display": "none"}
    btnSelectText = "◻️ Select"
    btnSelectColor = "primary"

    if mdl.isMulti and now.sim.assCur and mdl.curIdx < len(now.sim.assCur):
        fullAss = now.sim.assCur[mdl.curIdx]

        btnSelectStyle = {"display": "block"}
        isSelected = fullAss.selected if fullAss else False
        btnSelectText, btnSelectColor = _getSelectBtnState(isSelected)

    # Help panel state
    helpCss, helpTxt = _getHelpState(mdl.helpCollapsed)

    return mdl.open, htms, prevStyle, nextStyle, badgeStyle, badgeText, btnSelectStyle, btnSelectText, btnSelectColor, helpCss, helpTxt


@cbk(
    out(k.store, "data", allow_duplicate=True),
    inp({"type": "img-pop", "index": ALL}, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_OnImgPopClicked(clks, dta_mdl):
    if not clks or not any(clks): return noUpd

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


@cbk(
    [
        out(k.store, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp({"type": "img-pop-multi", "id": ALL, "autoId": ALL}, "n_clicks"),
    [
        ste(k.store, "data"),
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call=True
)
def mdlImg_OnImgPopMultiClicked(clks, dta_mdl, dta_now):
    if not clks or not any(clks): return noUpd.by(2)

    if not ctx.triggered: return noUpd.by(2)

    mdl = models.MdlImg.fromDict(dta_mdl)
    now = models.Now.fromDict(dta_now)

    trigIdx = ctx.triggered_id
    if isinstance(trigIdx, dict) and "id" in trigIdx:
        assId = trigIdx["id"]
        lg.info(f"[mdlImg] clicked, assId[{assId}] clicked[{clks}]")

        if assId and now.sim.assCur:
            mdl.open = True
            mdl.imgUrl = f"/api/img/{assId}?q=preview"
            mdl.isMulti = True
            mdl.curIdx = next((i for i, ass in enumerate(now.sim.assCur) if ass.id == assId), 0)

    return mdl.toDict(), now.toDict()


@cbk(
    [
        out(k.store, "data", allow_duplicate=True),
        out(k.content, "children", allow_duplicate=True),
        out(k.showIds, "children", allow_duplicate=True),
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
        ste(k.store, "data"),
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call=True
)
def mdlImg_OnNavClicked(clk_prev, clk_next, dta_mdl, dta_now):
    if not clk_prev and not clk_next: return noUpd.by(7)

    if not ctx.triggered: return noUpd.by(7)

    now = models.Now.fromDict(dta_now)
    mdl = models.MdlImg.fromDict(dta_mdl)

    if not mdl.isMulti or not now.sim.assCur: return noUpd.by(7)

    trgId = getTrgId()

    if trgId == k.btnPrev:
        if mdl.curIdx > 0:
            mdl.curIdx = mdl.curIdx - 1
        else:
            return noUpd.by(7)
    elif trgId == k.btnNext:
        if mdl.curIdx < len(now.sim.assCur) - 1:
            mdl.curIdx = mdl.curIdx + 1
        else:
            return noUpd.by(7)

    curAss = now.sim.assCur[mdl.curIdx]
    assId = curAss.id
    mdl.imgUrl = f"/api/img/{assId}?q=preview"

    # Rebuild content with new image
    htms, badgeText = _buildImageContent(mdl, now)
    prevStyle, nextStyle = _getNavStyles(mdl, now)

    # Get select button state
    ass = _getAssetBy(now, assId)
    isSelected = ass.selected if ass else False
    btnSelectText, btnSelectColor = _getSelectBtnState(isSelected)

    lg.info(f"[mdlImg] nav to idx[{mdl.curIdx}] assId[{assId}] autoId[{curAss.autoId} selected[{isSelected}]")

    return mdl.toDict(), htms, badgeText, prevStyle, nextStyle, btnSelectText, btnSelectColor


@cbk(
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
def mdlImg_OnSelectClicked(clks, dta_now, dta_mdl):
    if not clks: return noUpd.by(4)

    now = models.Now.fromDict(dta_now)
    mdl = models.MdlImg.fromDict(dta_mdl)

    if not mdl.isMulti or not now.sim.assCur or mdl.curIdx >= len(now.sim.assCur):
        return noUpd.by(4)

    curAss = now.sim.assCur[mdl.curIdx]
    assId = curAss.id

    if not assId or not now.sim.assCur:
        return noUpd.by(4)

    for ass in now.sim.assCur:
        if ass.id == assId:
            ass.selected = not ass.selected
            lg.info(f'[mdlImg:select] toggled: {ass.autoId}, selected: {ass.selected}')
            break

    selected = [ass for ass in now.sim.assCur if ass.selected]
    now.sim.assSelect = selected

    # Get the updated selected state
    ass = _getAssetBy(now, assId)
    isSelected = ass.selected if ass else False
    btnText, btnColor = _getSelectBtnState(isSelected)

    return now.toDict(), mdl.toDict(), btnText, btnColor


@cbk(
    [
        out(k.modal, "className"),
        out(k.btnMode, "children")
    ],
    inp(k.btnMode, "n_clicks"),
    ste(k.modal, "className"),
    prevent_initial_call=True
)
def mdlImg_ToggleMode(n_clicks, classes):
    if not n_clicks: return [noUpd.by(2)]

    if not classes: classes = ""

    hasClass = k.cssAuto in classes.split()

    if hasClass:
        css = " ".join([c for c in classes.split() if c != k.cssAuto])
        txt = k.txtHFix
    else:
        css = classes + f" {k.cssAuto}" if classes else k.cssAuto
        txt = k.txtHAuto

    return [css, txt]


@cbk(
    [
        out(k.store, "data", allow_duplicate=True),
        out(k.help, "className", allow_duplicate=True),
        out(k.btnHelp, "children", allow_duplicate=True),
    ],
    inp(k.btnHelp, "n_clicks"),
    ste(k.store, "data"),
    prevent_initial_call=True
)
def mdlImg_ToggleHelp(clks, dta_mdl):
    if not clks: return noUpd.by(3)

    mdl = models.MdlImg.fromDict(dta_mdl)
    mdl.helpCollapsed = not mdl.helpCollapsed

    helpCss, helpTxt = _getHelpState(mdl.helpCollapsed)

    return mdl.toDict(), helpCss, helpTxt
