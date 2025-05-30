from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd
from util import log
from mod import models, tskSvc
import db
from conf import ks

lg = log.get(__name__)

dash.register_page(
    __name__,
    path='/',
    title=f"{ks.title}: " + ks.pg.fetch.name,
)

class k:
    selectUsr = "fetch-usr-select"
    btnFetch = "fetch-btn-assets"
    btnClean = "fetch-btn-clear"
    btnReset = "fetch-btn-reset"

    initFetch = "fetch-init"


opts = []  #[{"label": "All Users", "value": ""}] # current no support

#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        dbc.Row([
            dbc.Col(htm.H3(f"{ks.pg.fetch.name}"), width=3),
            dbc.Col(htm.Small(f"{ks.pg.fetch.desc}", className="text-muted"))
        ], className="mb-4"),

        dbc.Card([
            dbc.CardHeader("Settings"),
            dbc.CardBody([
                htm.Div([
                    htm.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Select User"),
                                dcc.Dropdown(
                                    id=k.selectUsr,
                                    options=[],
                                    placeholder="Select user.",
                                    clearable=False
                                ),
                            ], width=12),
                        ]),
                    ]),
                ]),

            ])
        ], className="mb-4"),


        dbc.Row([
            dbc.Col([
                dbc.Button(
                    id=k.btnFetch,
                    color="primary",
                    size="lg",
                    className="w-100",
                    disabled=True,
                ),
                htm.Div(
                    "Asset that already exist locally will be skipped"
                    , className="p-2 text-center")
            ], width=5),

            dbc.Col([
                dbc.Button(
                    "---",
                    id=k.btnClean,
                    color="danger",
                    size="lg",
                    className="w-100",
                ),
            ], width=4),
            dbc.Col([
                htm.Div( "Please proceed with caution", className="txt-sm" ),
                dbc.Button(
                    "Reset All local data",
                    id=k.btnReset,
                    size="sm",
                    color="danger",
                    className="w-100",
                ),
            ], width=3),

        ], className="mb-4"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================


        # *[htm.Div(f"這是第 {i + 1} 個 div") for i in range(10)],

        dcc.Store(id=k.initFetch),
        #====== bottom end ======================================================
    ])


#========================================================================
dis_show = {"display": "block"}
dis_hide = {"display": "none"}

#========================================================================
@callback(
    [
        out(k.selectUsr, "options"),
        out(k.selectUsr, "value"),
    ],
    inp(k.initFetch, "data"),
    ste(ks.sto.now, "data"),
    prevent_initial_call="initial_duplicate"
)
def assets_Init(dta_pi, dta_now):
    now = models.Now.fromDict(dta_now)
    lg.info(f"[fth:init] usrId[{db.dto.usrId}] now[{now.usrId}]")

    opts = []
    usrs = db.psql.fetchUsers()
    if usrs and len(usrs) > 0:
        for usr in usrs:
            opts.append({"label": usr.name, "value": usr.id})

    return opts, db.dto.usrId


#------------------------------------------------------------------------
# Update button text and enabled status based on selected data source and user
#------------------------------------------------------------------------
@callback(
    [
        out(k.btnFetch, "children"),
        out(k.btnFetch, "disabled"),
        out(k.btnClean, "children"),
        out(k.btnClean, "disabled"),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(k.selectUsr, "value"),
        inp(ks.sto.cnt, "data"),
    ],
    ste(ks.sto.tsk, "data"),
    ste(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def assets_Status(usrId, dta_cnt, dta_tsk, dta_now, dta_nfy):
    tsk = models.Tsk.fromDict(dta_tsk)
    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)
    nfy = models.Nfy.fromDict(dta_nfy)


    hasData = cnt.vec > 0 or cnt.ass > 0

    isTasking = tsk.id is not None

    disBtnRun = isTasking
    disBtnClr = isTasking

    txtBtn = f"Fetch: Get Assets"
    txtClr = f"Clean Data"

    if usrId and usrId != now.usrId:
        usr = db.psql.fetchUser(usrId)
        if usr:
            db.dto.usrId = usrId
            now.usrId = usrId
            nfy.info(f"Switched user: {usr.name}")
        else:
            usrId = now.usrId = db.dto.usrId = None

    if isTasking:
        disBtnRun = disBtnClr = True
        txtBtn = "Task in progress..."

    if not now.usrId:
        disBtnRun = disBtnClr = True
        txtBtn = "Please select user"
        nfy.info( txtBtn )

    elif usrId == "":
        disBtnRun = disBtnClr = True
        txtBtn = "Please select user"
        txtClr = "---"
    else:
        if not now.usrId:
            disBtnRun = disBtnClr = True
            txtBtn = "--No users--"
        else:
            usr = db.psql.fetchUser(now.usrId)
            cntRemote = db.psql.count(now.usrId)
            cntLocal = db.pics.count(now.usrId)

            if cntLocal <= 0:
                disBtnClr = True

            disBtnRun = cntRemote <= cntLocal or cntRemote == 0

            txtBtn = f"Fetch: {usr.name} ({cntRemote})"
            txtClr = f"Clear local: {usr.name} ({cntLocal})"

    lg.info(f"[assets:status] usrId[{usrId}] cnt: {cnt}")

    return txtBtn, disBtnRun, txtClr, disBtnClr, now.toDict(), nfy.toDict()

#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(k.btnFetch, "n_clicks"),
        inp(k.btnClean, "n_clicks"),
        inp(k.btnReset, "n_clicks"),
    ],
    [
        ste(k.selectUsr, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def assets_RunModal(clk_feh, clk_clr, clk_rst, usrId, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not clk_feh and not clk_clr and not clk_rst: return noUpd, noUpd

    now = models.Now.fromDict(dta_now)
    mdl = models.Mdl.fromDict(dta_mdl)
    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)

    if tsk.id: return noUpd, noUpd
    trgSrc = getTriggerId()

    if trgSrc == k.btnReset:
        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.reset
        mdl.msg = [
            htm.Div([ htm.B('Warning:'), ' Reset all local data' ], className="p-5")
        ]
    elif trgSrc == k.btnClean:
        if not now.usrId:
            nfy.warn("not select user..")
            mdl.reset()
        else:
            usr = db.psql.fetchUser(now.usrId)
            cnt = db.pics.count( now.usrId )

            mdl.id = ks.pg.fetch
            mdl.cmd = ks.cmd.fetch.clear
            mdl.msg = f'Start clearing user[ {usr.name} ] assets[ {cnt} ]'

    elif trgSrc == k.btnFetch:
        if not now.usrId:
            nfy.warn("not select user..")
            mdl.reset()
        else:
            cnt = db.psql.count(now.usrId)
            usr = db.psql.fetchUser(now.usrId)

            mdl.id = ks.pg.fetch
            mdl.cmd = ks.cmd.fetch.asset
            mdl.msg = f"Start getting assets[ {cnt} ] for user[ {usr.name} ] ?"

    return mdl.toDict(), nfy.toDict()


#------------------------------------------------------------------------
#------------------------------------------------------------------------


#========================================================================
# task acts
#========================================================================
from mod import mapFns
from mod.models import IFnProg

#------------------------------------------------------------------------
def onFetchAssets(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt

    try:
        # todo: add support for all users?

        try:
            db.psql.chk()
        except Exception as e:
            msg = f"Error: Cannot connect to PostgreSQL database: {str(e)}"
            nfy.error(msg)
            return nfy, now, msg

        usr = db.psql.fetchUser(now.usrId)

        if not usr:
            msg = f"Error: User not found"
            nfy.error(msg)
            return nfy, now, msg

        doReport(5, f"Starting to fetch assets for {usr.name} from PostgreSQL")

        cntAll = db.psql.count(usr.id)
        if cntAll <= 0:
            msg = f"No assets found for {usr.name}"
            nfy.info(msg)
            return nfy, now, msg

        doReport(10, f"Found {cntAll} photos, starting to fetch assets")

        try:
            assets = db.psql.fetchAssets(usr, onUpdate=doReport)

        except Exception as e:
            msg = f"Error fetching assets for {usr.name}, {str(e)}"
            nfy.error(msg)
            return nfy, now, msg

        if not assets or len(assets) == 0:
            msg = f"No assets retrieved for {usr.name}"
            nfy.info(msg)
            return nfy, now, msg

        doReport(50, f"Retrieved {len(assets)} photos, starting to save to local database")

        cntFetch = len(assets)
        cntSaved = 0

        # updateIds = []
        # def onUpdAss( ass:models.Asset ):
        #     nonlocal updateIds
        #     updateIds.append( ass.id )

        with db.pics.mkConn() as conn:
            c = conn.cursor()
            for idx, asset in enumerate(assets):
                if idx % 10 == 0:
                    prog = 50 + int((idx / len(assets)) * 40)
                    doReport(prog, f"Saving photo {idx}/{len(assets)}")

                added = db.pics.saveBy(asset, c)
                if added: cntSaved += 1

            conn.commit()

        # clear update vecs
        # if len( updateIds ) > 0:
        #     db.vecs.deleteBy( updateIds )

        cnt.ass = db.pics.count()

        doReport(100, f"Saved {cntSaved} photos")

        msg = f"success, user[ {usr.name} ] fetched[ {cntFetch} ] and saved[ {cntSaved} ]"
        nfy.info(msg)

        return sto, msg

    except Exception as e:
        msg = f"Failed fetching assets: {str(e)}"
        nfy.error(msg)

        raise RuntimeError(msg)

#------------------------------------------------------------------------
def onFetchClear(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt

    msg = "[Assets:Clear] Successfully cleared all assets"
    import db

    try:
        db.psql.chk()
    except Exception as e:
        msg = f"Error: Cannot connect to PostgreSQL database: {str(e)}"
        nfy.error(msg)
        return nfy, now, msg

    try:
        usr = db.psql.fetchUser(now.usrId)
        if not usr:
            msg = f"Error: User not found"
            nfy.error(msg)
            return nfy, now, msg

        doReport(10, f"Starting clear assets for {usr.name}")

        assets = db.pics.getAllByUsrId(now.usrId)
        if not assets or len(assets) == 0:
            msg = f"No assets found for {usr.name}"
            return sto, msg

        assIds = [a.id for a in assets]
        #------------------------------------
        db.pics.clearBy(now.usrId)

        db.vecs.deleteBy(assIds)

        cnt.refreshFromDB()

        return sto, msg
    except Exception as e:
        msg = f"Failed to clear user data: {str(e)}"
        nfy.error(msg)
        raise RuntimeError(msg)
#------------------------------------------------------------------------
def onFetchReset(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt

    msg = "[Assets:Reset] Successfully"
    import db

    try:

        doReport(10, f"Starting reset assets")
        db.resetAllData()

        cnt.refreshFromDB()

        return sto, msg
    except Exception as e:
        msg = f"Failed to clear all data: {str(e)}"
        nfy.error(msg)
        raise RuntimeError(msg)


#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.fetch.asset] = onFetchAssets
mapFns[ks.cmd.fetch.clear] = onFetchClear
mapFns[ks.cmd.fetch.reset] = onFetchReset
