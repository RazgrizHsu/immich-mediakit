import db
from conf import ks
from dsh import dash, htm, cbk, dbc, inp, out, ste, getTrgId, noUpd
from util import log
from mod import models, mapFns, tskSvc

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.vector}',
    title=f"{ks.title}: " + ks.pg.vector.name,
)

class K:
    selectQ = "vector-selectPhotoQ"
    btnDoVec = "vector-btnDoVec"
    btnClear = "vector-btnClear"


#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        htm.Div([
            htm.H3(f"{ks.pg.vector.name}"),
            htm.Small(f"{ks.pg.vector.desc}", className="text-muted")
        ], className="body-header"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Processing Settings"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Photo Quality"),
                                dbc.Select(
                                    id=K.selectQ,
                                    options=[
                                        {"label": "Thumbnail (Fast)", "value": ks.db.thumbnail},
                                        {"label": "Preview", "value": ks.db.preview},
                                        {"label": "FullSize (Slow)", "value": ks.db.fullsize},
                                    ],
                                    value=db.dto.photoQ,
                                    className="mb-3",
                                ),
                            ], width=12),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                htm.Ul([
                                    htm.Li([htm.B("Thumbnail"), htm.Small(" Fastest, but with lower detail comparison accuracy"), ]),
                                    htm.Li([htm.B("Preview"), htm.Small(" Medium quality, generally the most balanced option"), ]),
                                    htm.Li([htm.B("FullSize"), htm.Small(" Slowest, but provides the most precise detail comparison"), ]),
                                ]),
                            ], width=12, className=""),
                        ], className="mb-0"),
                    ])
                ], className="mb-4")
            ], width=12),
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Execute: Process Assets",
                    id=K.btnDoVec,
                    color="primary",
                    size="lg",
                    className="w-100",
                    disabled=True,
                ),
            ], width=6),

            dbc.Col([
                dbc.Button(
                    "Clear All Vectors",
                    id=K.btnClear,
                    color="danger",
                    size="lg",
                    className="w-100",
                    disabled=True,
                ),
            ], width=6),
        ], className="mb-4"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #====== bottom end ======================================================
    ])


#========================================================================
# Page initialization
#========================================================================
@cbk(
    [
        out(K.btnDoVec, "children"),
        out(K.btnDoVec, "disabled"),
        out(K.btnClear, "disabled"),
        out(K.selectQ, "disabled"),
    ],
    inp(ks.sto.cnt, "data"),
    prevent_initial_call=False
)
def vec_OnInit(dta_cnt):
    cnt = models.Cnt.fromDict(dta_cnt)

    hasPics = cnt.ass > 0
    hasVecs = cnt.vec > 0

    btnTxt = "Execute - Process Assets"
    disBtnRun = True
    disBtnClr = True
    disSelect = False

    if hasVecs:
        btnTxt = "Vectors Complete"
        disBtnRun = True
        disBtnClr = False
        disSelect = True
    elif hasPics:
        btnTxt = "Execute - Process Assets"
        disBtnRun = False
        disBtnClr = True
    else:
        btnTxt = "Please Get Assets First"
        disBtnRun = True
        disBtnClr = True

    return btnTxt, disBtnRun, disBtnClr, disSelect


#------------------------------------------------------------------------
#------------------------------------------------------------------------
@cbk(
    [
        out(K.btnDoVec, "children", allow_duplicate=True),
        out(K.btnDoVec, "disabled", allow_duplicate=True),
        out(K.btnClear, "disabled", allow_duplicate=True),
        out(K.selectQ, "disabled", allow_duplicate=True),
    ],
    [
        inp(ks.sto.tsk, "data"),
    ],
    [
        ste(ks.sto.cnt, "data"),
    ],
    prevent_initial_call=True
)
def vec_Status(dta_tsk, dta_cnt):
    # trgId = getTrgId()
    # if trgId == ks.sto.tsk and not dta_tsk.get('id'): return noUpd.rep(5)

    tsk = models.Tsk.fromDict(dta_tsk)
    cnt = models.Cnt.fromDict(dta_cnt)

    isTskin = tsk.name is not None

    cntNeedVec = cnt.ass - cnt.vec

    disBtnRun = isTskin or cntNeedVec <= 0
    disBtnClr = isTskin or cnt.vec <= 0
    disPhotoQ = isTskin or cnt.vec >= 1
    txtBtn = f"Process Assets( {cntNeedVec} )" if cntNeedVec else "No Asset Need it"

    lg.info(f"[vec] vec[{cnt.vec}] select[{disPhotoQ}]")

    if tsk.id:
        txtBtn = "Task in progress.."

    return txtBtn, disBtnRun, disBtnClr, disPhotoQ

#------------------------------------------------------------------------
#------------------------------------------------------------------------
@cbk(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    [
        inp(K.btnDoVec, "n_clicks"),
        inp(K.btnClear, "n_clicks"),
    ],
    [
        ste(K.selectQ, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.cnt, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def vec_RunModal(nclk_proc, nclk_clear, photoQ, dta_now, dta_cnt, dta_mdl, dta_tsk, dta_nfy):
    if not nclk_proc and not nclk_clear: return noUpd.by(3)

    trgId = getTrgId()
    if trgId == ks.sto.tsk and not dta_tsk.get('id'): return noUpd.by(3)

    tsk = models.Tsk.fromDict(dta_tsk)
    if tsk.id: return noUpd.by(3)

    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)
    mdl = models.Mdl.fromDict(dta_mdl)
    nfy = models.Nfy.fromDict(dta_nfy)

    lg.info(f"[vec] trig[{trgId}] clk[{nclk_proc}/{nclk_clear}] tsk[{tsk}]")

    if trgId == K.btnDoVec:
        if cnt.ass <= 0:
            nfy.error("No asset data to process")
        else:
            mdl.id = ks.pg.vector
            mdl.cmd = ks.cmd.vec.toVec
            mdl.msg = f"Begin processing photos[{cnt.ass - cnt.vec}] with quality[{photoQ}] ?"

            db.dto.photoQ = photoQ

    elif trgId == K.btnClear:
        if cnt.vec <= 0:
            nfy.error("No vector data to clear")
        else:
            mdl.id = ks.pg.vector
            mdl.cmd = ks.cmd.vec.clear
            mdl.msg = [
                "Are you sure you want to clear all vectors?"
            ]

    return mdl.toDict(), nfy.toDict(), now.toDict()


#========================================================================
# task acts
#========================================================================
import imgs
from mod.models import IFnProg

def vec_ToVec(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    msg = "[vec] Processing successful"

    try:
        photoQ = db.dto.photoQ

        doReport(1, f"Initializing with photoQ[{photoQ}]")

        assets = db.pics.getAllNonVector()
        doReport(5, f"Getting asset data count[{len(assets)}]")

        if not assets or len(assets) == 0:
            msg = "No assets to process"
            nfy.error(msg)
            return nfy, now, msg

        cntAll = len(assets)
        doReport(8, f"Found [ {cntAll} ] starting processing")

        rst = imgs.processVectors(assets, photoQ, onUpdate=doReport)

        cnt.vec = db.vecs.count()

        msg = f"Completed: total[ {rst.total} ] done[ {rst.done} ] Skip[ {rst.skip} ]"
        if rst.error: msg += f" Error[ {rst.error}]"

        nfy.success(msg)

        return sto, msg

    except Exception as e:
        msg = f"Asset processing failed: {str(e)}"
        nfy.error(msg)
        raise RuntimeError(msg)


def vec_Clear(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    msg = "[AssetVec] Clearing successful"

    try:
        doReport(10, "Preparing to clear all Vectors")

        if cnt.vec <= 0:
            msg = "No vector data to clear"
            nfy.warn(msg)
            return nfy, now, msg

        doReport(30, "Clearing Vectors...")

        count = db.vecs.count()
        if count >= 0:
            db.vecs.cleanAll()
            db.pics.clearAllVectored()

        doReport(90, f"Cleared {count} vector records")

        cnt.vec = 0

        msg = f"Successfully cleared all photo vector data ({count} records)"
        nfy.success(msg)

        doReport(100, "Clearing complete")
        return sto, msg

    except Exception as e:
        msg = f"Failed to clear vectors: {str(e)}"
        nfy.error(msg)
        raise RuntimeError(msg)

#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.vec.toVec] = vec_ToVec
mapFns[ks.cmd.vec.clear] = vec_Clear
