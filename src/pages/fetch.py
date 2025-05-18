from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd
from util import log, models, task
import db
from conf import Ks

lg = log.get(__name__)

dash.register_page(
    __name__,
    path='/',
    title='Source Fetch',
    name='Source Fetch'
)

class K:
    selectUsrId = "inp-user-selector"
    btnFetch = "btn-assets-fetch"
    btnClean = "btn-assets-clear"


opts = [{"label": "All Users", "value": ""}]


#========================================================================
def layout():
    return htm.Div([
        htm.H3("Srouce Fetch", className="mb-4"),

        htm.Div([
            htm.P(
                f"Get photo asset from (Api/Psql) and save to local db",
                className="mb-4"
            ),

            # Settings area
            dbc.Card([
                dbc.CardHeader("Settings"),
                dbc.CardBody([
                    # dbc.Row([
                    #     dbc.Col([
                    #         dbc.Label("Data Source"),
                    #         dbc.RadioItems(
                    #             id=K.selectUseType,
                    #             options=[
                    #                 {"label": Ks.use.api, "value": Ks.use.api},
                    #                 {"label": Ks.use.dir, "value": Ks.use.dir}
                    #             ],
                    #             value=Ks.use.api,
                    #             inline=True,
                    #             className="mb-3"
                    #         ),
                    #     ], width=12),
                    # ]),

                    htm.Div([
                        htm.Div([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select User"),
                                    dcc.Dropdown(
                                        id=K.selectUsrId,
                                        options=opts,
                                        placeholder="Select user (defaults to all users)",
                                        value="",
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
                        id=K.btnFetch,
                        color="primary",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),

                dbc.Col([
                    dbc.Button(
                        "Clear All Asset Data",
                        id=K.btnClean,
                        color="danger",
                        size="lg",
                        className="w-100",
                    ),
                ], width=6),
            ], className="mb-4"),

        ]),
    ])


#========================================================================
dis_show = {"display": "block"}
dis_hide = {"display": "none"}

#========================================================================
@callback(
    [
        out(K.selectUsrId, "options"),
        out(K.selectUsrId, "value"),
    ],
    inp(Ks.store.now, "data"),
    ste(K.selectUsrId, "options")
)
def assets_Init(dta_now, opts):
    # lg.info("[Assets] Initialization: PageInit by Sess")

    now = models.Now.fromStore(dta_now)

    if len(opts) <= 1:  # Only refill if there's just 1 option
        usrs = now.usrs
        if usrs and len(usrs) > 0:
            for usr in usrs:
                opts.append({"label": usr.name, "value": usr.id})

    # lg.info( f"[fetch:init] now.usr: {now.usr} type({type(now.usr)}) opts: {opts}" )

    usrId = now.usr.id if now and now.usr else ""

    return opts, usrId


#------------------------------------------------------------------------
# Update button text and enabled status based on selected data source and user
#------------------------------------------------------------------------
@callback(
    [
        out(K.btnFetch, "children"),
        out(K.btnFetch, "disabled"),
        out(K.btnClean, "disabled"),
        out(Ks.store.now, "data", allow_duplicate=True),
        out(Ks.store.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(K.selectUsrId, "value"),
        inp(Ks.store.tsk, "data"),
    ],
    ste(Ks.store.now, "data"),
    ste(Ks.store.nfy, "data"),
    prevent_initial_call=True
)
def assets_Status(usrId, dta_tsk, dta_now, dta_nfy):

    tsk = models.Tsk.fromStore(dta_tsk)
    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)

    # lg.info(f"[assets] Status: useType[{useType}] usrId[{usrId}] apiKey[{apiKey}]")

    hasData = now.cntVec > 0 or now.cntPic > 0

    isTasking = tsk.id is not None

    disBtnRun = isTasking
    disBtnClr = isTasking or (not hasData)

    txtBtn = f"Fetch: Get Assets"

    if now.usr and usrId != now.usr.id:
        db.dyn.dto.usrId = usrId
        now.switchUsr(usrId)
        nfy.info(f"Switched user: {'All Users' if not now.usr else now.usr.name}")

    if isTasking:
        disBtnRun = True
        txtBtn = "Task in progress..."

    if not usrId and usrId != "":
        disBtnRun = True
        txtBtn = "Please select user"

    elif usrId == "":
        txtBtn = "Fetch: All Users"
    else:
        if not now.usrs:
            disBtnRun = True
            txtBtn = "--No users--"

        else:
            if now.usr: txtBtn = f"Fetch: {now.usr.name}"

    return txtBtn, disBtnRun, disBtnClr, now.toStore(), nfy.toStore()

#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(Ks.store.mdl, "data", allow_duplicate=True),
        out(Ks.store.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(K.btnFetch, "n_clicks"),
        inp(K.btnClean, "n_clicks"),
    ],
    [
        ste(K.selectUsrId, "value"),
        ste(Ks.store.now, "data"),
        ste(Ks.store.mdl, "data"),
        ste(Ks.store.tsk, "data"),
        ste(Ks.store.nfy, "data"),
    ],
    prevent_initial_call=True
)
def assets_BtnRunModals(nclk_fetch, nclk_clean, usrId, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not nclk_fetch and not nclk_clean: return noUpd, noUpd

    now = models.Now.fromStore(dta_now)
    mdl = models.Mdl.fromStore(dta_mdl)
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)

    if tsk.id: return noUpd, noUpd
    trgSrc = getTriggerId()
    lg.info(f"[srcFetch] trgSrc[{trgSrc}]")


    if trgSrc == K.btnClean:
        nfy.info(f"[assets] Triggered: Clear all asset data")

        mdl.id = 'assets'
        mdl.cmd = 'clear'
        mdl.msg = 'Start clearing all asset data'

    elif trgSrc == K.btnFetch:
        mdl.id = 'assets'
        mdl.cmd = 'fetch'
        if now.usr:
            mdl.msg = f"Start getting assets for user [{now.usr.name}] from PostgreSQL"
        else:
            mdl.msg = "Start getting assets for all users from PostgreSQL"

    return mdl.toStore(), nfy.toStore()


#------------------------------------------------------------------------
#------------------------------------------------------------------------



#========================================================================
# register & trigger actions
#========================================================================
from util.task import IFnProg

#------------------------------------------------------------------------
def onFetchAssets(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    try:
        onUpdate(5, "5%", "init connection")

        if not db.psql.conn:
            msg = "Error: Cannot connect to PostgreSQL database"
            nfy.error(msg)
            return nfy, now, msg

        usr = now.usr

        if not usr:
            msg = f"Error: User not found"
            nfy.error(msg)
            return nfy, now, msg

        else:
            db.pics.deleteUsrAssets(now.usr.id)

        onUpdate(10, "10%", f"Starting to fetch assets for {now.usr.name} from PostgreSQL")

        cntAll = db.psql.countAssets(now.usr.id)
        if cntAll <= 0:
            msg = f"No assets found for {now.usr.name}"
            nfy.info(msg)
            return nfy, now, msg

        onUpdate(15, "15%", f"Found {cntAll} photos, starting to fetch assets")

        assets = db.psql.fetchAssets(now.usr.id)

        if not assets or len(assets) == 0:
            msg = f"No assets retrieved for {now.usr.name}"
            nfy.info(msg)
            return nfy, now, msg

        onUpdate(50, "50%", f"Retrieved {len(assets)} photos, starting to save to local database")

        cntSaved = 0
        for idx, asset in enumerate(assets):
            if idx % 10 == 0:
                progress = 50 + int((idx / len(assets)) * 40)
                onUpdate(progress, f"{progress}%", f"Saving photo {idx}/{len(assets)}")

            db.pics.saveBy(asset)
            cntSaved += 1

        now.cntPic = db.pics.count()

        onUpdate(100, "100%", f"Saved {cntSaved} photos")

        msg = f"Successfully fetched and saved {cntSaved} photos from PostgreSQL"
        nfy.info(msg)

        return nfy, now, msg

    except Exception as e:
        msg = f"Error fetching PostgreSQL assets: {str(e)}"
        nfy.error(msg)
        return nfy, now, f"Error: {msg}"

#------------------------------------------------------------------------
def onFetchClearAll(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    lg.info(f"[assets] Final execution.. onFetchClearAll: tsk[{tsk.id}]")

    msg = "[Assets:Clear] Successfully cleared all assets"
    import db
    try:
        onUpdate(10, "10%", f"start clear..")
        db.clear_all_data()
        now.cntPic = 0
        now.cntVec = 0
    except Exception as e:
        msg = f"Failed to clear all asset data: {str(e)}"
        nfy.error(msg)
        return nfy, now, msg

    return nfy, now, msg

#========================================================================
# Set up global functions
#========================================================================
task.mapFns['fetch_assets_psql'] = onFetchAssets
task.mapFns['fetch_assets_clear'] = onFetchClearAll
