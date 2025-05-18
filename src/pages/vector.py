import db
from dsh import dash, htm, callback, dbc, inp, out, ste, getTriggerId, noUpd
from util import log, models, task

from conf import Ks, envs

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{Ks.pgs.photoVec}',
    title='Vectors',
    name='Vectors'
)

class K:
    selectQ = "sel-photoQ"
    btnProcess = "btn-process-photos"
    btnClear = "btn-clear-vectors"
    txtDA = "txt-direct-access"


#========================================================================
def layout():
    return htm.Div([
        htm.H3("Generate Vectors", className="mb-4"),

        htm.Div([
            htm.P(
                "Process photos to generate feature vectors for similarity calculations. This step reads each photo and generates a 2048-dimensional vector.",
                className="mb-4"
            ),

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
                                            {"label": "Thumbnail (Fast)", "value": Ks.db.thumbnail},
                                            {"label": "Preview", "value": Ks.db.preview},
                                            {"label": "FullSize (Slow)", "value": Ks.db.fullsize},
                                        ],
                                        value=Ks.db.preview,
                                        className="mb-3",
                                    ),
                                ], width=12),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col([
                                    htm.Ul([
                                    htm.Li( [htm.B( "Thumbnail" ),htm.Small( " Fastest, but with lower detail comparison accuracy" ), ]),
                                    htm.Li( [htm.B( "Preview" ),htm.Small( " Medium quality, generally the most balanced option" ), ]),
                                    htm.Li( [htm.B( "FullSize" ),htm.Small( " Slowest, but provides the most precise detail comparison" ), ]),
                                    ]),
                                ], width=12, className=""),
                            ], className="mb-0"),
                        ])
                    ], className="mb-4")
                ], width=8),
                dbc.Col([

                    dbc.Card([
                        dbc.CardHeader("env"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    htm.Small([
                                        "IMMICH_PATH : ",
                                        htm.Span(f"{envs.immichPath if envs.immichPath else '--none--'}", className="tag" ),
                                    ]),
                                ], width=12),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col([
                                    htm.Small([
                                        "Direct Access : ",
                                        htm.Span("connect..", className="tag", id=K.txtDA ),
                                    ]),
                                ], width=12),
                            ], className="mb-2"),
                        ])
                    ], className="mb-4"),

                ]),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Execute: Process Assets",
                        id=K.btnProcess,
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
        ]),
    ])


#========================================================================
# Page initialization
#========================================================================
@callback(
    [
        out(K.btnProcess, "children"),
        out(K.btnProcess, "disabled"),
        out(K.btnClear, "disabled"),
        out(K.txtDA, "children" ),
        out(K.txtDA, "style" ),
    ],
    inp(Ks.store.now, "data"),
    prevent_initial_call=False
)
def photoVec_OnInit(dta_now):
    now = models.Now.fromStore(dta_now)

    hasPics = now.cntPic > 0
    hasVecs = now.cntVec > 0

    btnTxt = "Execute - Process Assets"
    daTxt = "testing..."
    daSty = {}
    disBtnRun = True
    disBtnClr = True

    if hasVecs:
        btnTxt = "Vector Processing Complete"
        disBtnRun = True
        disBtnClr = False
    elif hasPics:
        btnTxt = "Execute - Process Assets"
        disBtnRun = False
        disBtnClr = True
    else:
        btnTxt = "Please Get Photo Assets First"
        disBtnRun = True
        disBtnClr = True

    if hasPics:
        rst = imgs.testDirectAccess()
        daSty = { 'background': '#78c22a', 'padding': '3px 5px 2px 5px' } if rst.startswith( "OK" ) else { 'background': '#8A0100' }

    return btnTxt, disBtnRun, disBtnClr, rst, daSty


#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(K.btnProcess, "children", allow_duplicate=True),
        out(K.btnProcess, "disabled", allow_duplicate=True),
        out(K.btnClear, "disabled", allow_duplicate=True),
        out(Ks.store.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(K.btnProcess, "n_clicks"),
        inp(K.btnClear, "n_clicks"),
        inp(Ks.store.tsk, "data"),
    ],
    [
        ste(Ks.store.now, "data"),
        ste(Ks.store.nfy, "data"),
    ],
    prevent_initial_call=True
)
def photoVec_Status(nclk_proc, nclk_clear, dta_tsk, dta_now, dta_nfy):
    trgId = getTriggerId()
    if not trgId or (not nclk_proc and not nclk_clear): return noUpd, noUpd, noUpd, noUpd
    if trgId == Ks.store.tsk and not dta_tsk.get('id'): return noUpd, noUpd, noUpd, noUpd

    tsk = models.Tsk.fromStore(dta_tsk)
    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)

    hasData = now.cntPic > 0
    isTskin = tsk.id is not None

    txtBtn = "Execute: Process Assets"
    disBtnRun = isTskin or not hasData
    disBtnClr = isTskin or now.cntVec <= 0

    if tsk.id:
        nfy.error(f"task already running, id[{tsk.id}] name[{tsk.name}] keyFn[{tsk.keyFn}] trgId[{trgId}]")
        txtBtn = "Task in progress.."

    return txtBtn, disBtnRun, disBtnClr, nfy.toStore()

#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(Ks.store.mdl, "data", allow_duplicate=True),
        out(Ks.store.nfy, "data", allow_duplicate=True),
        out(Ks.store.now, "data", allow_duplicate=True),
    ],
    [
        inp(K.btnProcess, "n_clicks"),
        inp(K.btnClear, "n_clicks"),
    ],
    [
        ste(K.selectQ, "value"),
        ste(Ks.store.now, "data"),
        ste(Ks.store.mdl, "data"),
        ste(Ks.store.tsk, "data"),
        ste(Ks.store.nfy, "data"),
    ],
    prevent_initial_call=True
)
def photoVec_BtnRunModals(nclk_proc, nclk_clear, photoQ, dta_now, dta_mdl, dta_tsk, dta_nfy):

    if not nclk_proc and not nclk_clear: return noUpd, noUpd, noUpd

    trgId = getTriggerId()
    if trgId == Ks.store.tsk and not dta_tsk.get('id'): return noUpd, noUpd, noUpd

    now = models.Now.fromStore(dta_now)
    mdl = models.Mdl.fromStore(dta_mdl)
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)

    if tsk.id: return noUpd, noUpd

    lg.info( f"[photoVec] trig[{trgId}] clk[{nclk_proc}/{nclk_clear}] tsk[{tsk}]" )


    if trgId == K.btnProcess:
        if now.cntPic <= 0:
            nfy.error("No asset data to process")
        else:
            mdl.id = 'photovec'
            mdl.cmd = 'process'
            mdl.msg = f"Begin vector processing for {now.cntPic} photos with {photoQ} quality?\n"
            mdl.msg += f"Note: Any existing vectors will be cleared first"
            now.photoQ = photoQ

    elif trgId == K.btnClear:
        if now.cntVec <= 0:
            nfy.error("No vector data to clear")
        else:
            nfy.info(f"[photoVec] Triggered: Clear all vectors")
            mdl.id = 'photovec'
            mdl.cmd = 'clear'
            mdl.msg = "Are you sure you want to clear all vectors?"

    return mdl.toStore(), nfy.toStore(), now.toStore()


#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(Ks.store.mdl, "data", allow_duplicate=True),
        out(Ks.store.tsk, "data", allow_duplicate=True),
        out(Ks.store.nfy, "data", allow_duplicate=True),
    ],
    [
        inp(Ks.store.mdl, "data"),
        inp(K.selectQ, "value"),
    ],
    [
        ste(Ks.store.now, "data"),
        ste(Ks.store.nfy, "data"),
    ],
    prevent_initial_call=True
)
def photoVec_RunActs(dta_mdl, photoQuality, dta_now, dta_nfy):
    mdl = models.Mdl.fromStore(dta_mdl)
    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)
    tsk = models.Tsk()

    if mdl.id == 'photovec' and mdl.ok:
        if mdl.cmd == 'process':
            tsk.id = 'photovec'
            tsk.name = 'Photo Vector Processing'
            tsk.keyFn = 'photoVec_ToVec'

            tsk.args = {
                "photoQuality": photoQuality
            }

            mdl.reset()
            nfy.info("Starting task: Photo Vector Processing")

        elif mdl.cmd == 'clear':
            tsk.id = 'photoVec_Clear'
            tsk.name = 'Clear Vectors'
            tsk.keyFn = 'photoVec_Clear'

            mdl.reset()
            nfy.info("Starting task: Clear Vectors")

    return mdl.toStore(), tsk.toStore(), nfy.toStore()


#========================================================================
# register & trigger actions
#========================================================================
import imgs
from util.task import IFnProg

def photoVec_ToVec(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    msg = "[PhotoVec] Processing successful"

    try:
        photoQ = now.photoQ if now.photoQ else Ks.db.thumbnail

        onUpdate(1, "1%", f"Initializing with photoQ[{photoQ}]")

        useType = now.useType

        onUpdate(5, "5%", f"Getting asset data count[{now.cntPic}]")
        assets = db.pics.getAll()

        if now.cntVec:
            db.vecs.clear()

        if not assets or len(assets) == 0:
            msg = "No assets to process"
            nfy.error(msg)
            return nfy, now, msg

        cntAll = len(assets)
        onUpdate(8, "", f"Found {cntAll} photos, starting processing")

        rst = imgs.processPhotoToVectors(assets, photoQ, onUpdate=onUpdate)

        now.cntVec = db.vecs.count()

        msg = f"Completed: total[{rst.total}] done[{rst.done}, Skip[{rst.skip}] Error[{rst.error}]"
        nfy.success(msg)

        return nfy, now, msg

    except Exception as e:
        msg = f"Photo processing failed: {str(e)}"
        nfy.error(msg)
        return nfy, now, msg


def photoVec_Clear(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    msg = "[PhotoVec] Clearing successful"

    try:
        onUpdate(10, "10%", "Preparing to clear all Vectors")

        if now.cntVec <= 0:
            msg = "No vector data to clear"
            nfy.warn(msg)
            return nfy, now, msg

        onUpdate(30, "30%", "Clearing Vectors...")

        count = db.vecs.count()
        if count >= 0:
            db.vecs.clear()

        onUpdate(90, "90%", f"Cleared {count} vector records")

        now.cntVec = 0

        msg = f"Successfully cleared all photo vector data ({count} records)"
        nfy.success(msg)

        onUpdate(100, "100%", "Clearing complete")
        return nfy, now, msg

    except Exception as e:
        msg = f"Failed to clear vectors: {str(e)}"
        nfy.error(msg)
        return nfy, now, msg

#========================================================================
# Set up global functions
#========================================================================
task.mapFns['photoVec_ToVec'] = photoVec_ToVec
task.mapFns['photoVec_Clear'] = photoVec_Clear
