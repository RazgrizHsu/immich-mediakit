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

    initFetch = "fetch-init"


opts = []  #[{"label": "All Users", "value": ""}] # current no support

#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        htm.H3(ks.pg.fetch.name, className="mb-4"),
        htm.P(ks.pg.fetch.desc, className="mb-4"),

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
            ], width=6),

            dbc.Col([
                dbc.Button(
                    "Clear All Asset Data",
                    id=k.btnClean,
                    color="danger",
                    size="lg",
                    className="w-100",
                ),
            ], width=6),
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
    # lg.info("[Assets] Initialization: PageInit by Sess")

    now = models.Now.fromDict(dta_now)

    opts = []
    usrs = db.psql.fetchUsers()
    if usrs and len(usrs) > 0:
        for usr in usrs:
            opts.append({"label": usr.name, "value": usr.id})

    return opts, db.dyn.dto.usrId


#------------------------------------------------------------------------
# Update button text and enabled status based on selected data source and user
#------------------------------------------------------------------------
@callback(
    [
        out(k.btnFetch, "children"),
        out(k.btnFetch, "disabled"),
        out(k.btnClean, "disabled"),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(k.selectUsr, "value"),
    ],
    ste(ks.sto.tsk, "data"),
    ste(ks.sto.now, "data"),
    ste(ks.sto.cnt, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def assets_Status(usrId, dta_tsk, dta_now, dta_cnt, dta_nfy):
    tsk = models.Tsk.fromDict(dta_tsk)
    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)
    nfy = models.Nfy.fromDict(dta_nfy)

    # lg.info(f"[assets] Status: usrId[{usrId}]")

    hasData = cnt.vec > 0 or cnt.ass > 0

    isTasking = tsk.id is not None

    disBtnRun = isTasking
    disBtnClr = isTasking or (not hasData)

    txtBtn = f"Fetch: Get Assets"

    if usrId and usrId != now.usrId:
        db.dyn.dto.usrId = usrId
        now.usrId = usrId
        #nfy.info(f"Switched user: {'All Users' if not now.usr else usr.name}")

    if isTasking:
        disBtnRun = True
        txtBtn = "Task in progress..."

    if not usrId:
        disBtnRun = True
        txtBtn = "Please select user"

    elif usrId == "":
        # cnt = db.psql.count()
        # txtBtn = f"Fetch: All ({cnt})"
        disBtnRun = True
        txtBtn = "Please select user"
    else:
        if not usrId:
            disBtnRun = True
            txtBtn = "--No users--"

        else:
            cnt = db.psql.count(now.usrId)
            usr = db.psql.fetchUser(now.usrId)
            txtBtn = f"Fetch: {usr.name} ({cnt})"

    return txtBtn, disBtnRun, disBtnClr, now.toDict(), nfy.toDict()

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
def assets_RunModal(nclk_fetch, nclk_clean, usrId, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not nclk_fetch and not nclk_clean: return noUpd, noUpd

    now = models.Now.fromDict(dta_now)
    mdl = models.Mdl.fromDict(dta_mdl)
    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)

    if tsk.id: return noUpd, noUpd
    trgSrc = getTriggerId()

    if trgSrc == k.btnClean:
        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.clear
        mdl.msg = 'Start clearing all asset data'

    elif trgSrc == k.btnFetch:
        if now.usrId:
            cnt = db.psql.count(now.usrId)
            usr = db.psql.fetchUser(now.usrId)

            mdl.id = ks.pg.fetch
            mdl.cmd = ks.cmd.fetch.asset
            mdl.msg = f"Start getting assets[{cnt}] for user [{usr.name}] ?"
        else:
            nfy.warn("not select user..")
        # else:
        #     cnt = db.psql.count()
        #     mdl.msg = f"Start getting all users assets count[{cnt}] ?"

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
        doReport(5, "init connection")

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

        # todo: add support for all users?

        db.pics.deleteForUsr(usr.id)

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

        cntSaved = 0
        for idx, asset in enumerate(assets):
            if idx % 10 == 0:
                prog = 50 + int((idx / len(assets)) * 40)
                doReport(prog, f"Saving photo {idx}/{len(assets)}")

            db.pics.saveBy(asset)
            cntSaved += 1

        cnt.ass = db.pics.count()

        doReport(100, f"Saved {cntSaved} photos")

        msg = f"Successfully fetched and saved {cntSaved} photos from PostgreSQL"
        nfy.info(msg)

        return sto, msg

    except Exception as e:
        msg = f"Failed fetching assets: {str(e)}"
        nfy.error(msg)

        raise RuntimeError(msg)

#------------------------------------------------------------------------
def onFetchClearAll(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now = sto.nfy, sto.now

    msg = "[Assets:Clear] Successfully cleared all assets"
    import db
    try:
        doReport(10, f"start clear..")
        db.clear_all_data()

        return sto, msg
    except Exception as e:
        msg = f"Failed to clear all data: {str(e)}"
        nfy.error(msg)
        raise RuntimeError(msg)


#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.fetch.asset] = onFetchAssets
mapFns[ks.cmd.fetch.clear] = onFetchClearAll
