from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd
from util import log, models, task
import db
from conf import ks

lg = log.get(__name__)

dash.register_page(
    __name__,
    path='/',
    title=f"{ks.title}: " + ks.pg.fetch.name,
)

class K:
    selectUsr = "inp-user-selector"
    btnFetch = "btn-assets-fetch"
    btnClean = "btn-assets-clear"

    pageInit = "fetch-page-init"


opts = [] #[{"label": "All Users", "value": ""}] # current no support


#========================================================================
def layout():
    return htm.Div([
        htm.H3(ks.pg.fetch.name, className="mb-4"),

        htm.Div([
            htm.P( ks.pg.fetch.desc, className="mb-4" ),

            dbc.Card([
                dbc.CardHeader("Settings"),
                dbc.CardBody([
                    htm.Div([
                        htm.Div([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select User"),
                                    dcc.Dropdown(
                                        id=K.selectUsr,
                                        options=opts,
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
        dcc.Store( id=K.pageInit ),
    ])


#========================================================================
dis_show = {"display": "block"}
dis_hide = {"display": "none"}

#========================================================================
@callback(
    [
        out(K.selectUsr, "options"),
        out(K.selectUsr, "value"),
    ],
    inp(K.pageInit, "data"),
    ste(ks.sto.now, "data"),
    ste(K.selectUsr, "value"),
    ste(K.selectUsr, "options")
)
def assets_Init(dta_pi, dta_now, selId, opts):
    # lg.info("[Assets] Initialization: PageInit by Sess")

    now = models.Now.fromStore(dta_now)

    if len(opts) <= 1:  # Only refill if there's just 1 option
        usrs = now.usrs
        if usrs and len(usrs) > 0:
            for usr in usrs:
                opts.append({"label": usr.name, "value": usr.id})

    return opts, db.dyn.dto.usrId


#------------------------------------------------------------------------
# Update button text and enabled status based on selected data source and user
#------------------------------------------------------------------------
@callback(
    [
        out(K.btnFetch, "children"),
        out(K.btnFetch, "disabled"),
        out(K.btnClean, "disabled"),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(K.selectUsr, "value"),
        inp(ks.sto.tsk, "data"),
    ],
    ste(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def assets_Status(usrId, dta_tsk, dta_now, dta_nfy):

    tsk = models.Tsk.fromStore(dta_tsk)
    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)

    # lg.info(f"[assets] Status: usrId[{usrId}]")

    hasData = now.cntVec > 0 or now.cntPic > 0

    isTasking = tsk.id is not None

    disBtnRun = isTasking
    disBtnClr = isTasking or (not hasData)

    txtBtn = f"Fetch: Get Assets"

    if usrId and usrId != ( now.usr.id if now and now.usr else None ):
        db.dyn.dto.usrId = usrId
        now.switchUsr(usrId)
        if now.usr:
            if not now.usr.key:
                nfy.warn(f"Switched user: {now.usr.name} key is None")
            else:
                nfy.info(f"Switched user: {now.usr.name}")
        #nfy.info(f"Switched user: {'All Users' if not now.usr else now.usr.name}")

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
        if not now.usrs:
            disBtnRun = True
            txtBtn = "--No users--"

        else:
            if now.usr:
                cnt = db.psql.count(now.usr.id)
                txtBtn = f"Fetch: {now.usr.name} ({cnt})"

    return txtBtn, disBtnRun, disBtnClr, now.toStore(), nfy.toStore()

#------------------------------------------------------------------------
#------------------------------------------------------------------------
@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True)
    ],
    [
        inp(K.btnFetch, "n_clicks"),
        inp(K.btnClean, "n_clicks"),
    ],
    [
        ste(K.selectUsr, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def assets_RunModal(nclk_fetch, nclk_clean, usrId, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not nclk_fetch and not nclk_clean: return noUpd, noUpd

    now = models.Now.fromStore(dta_now)
    mdl = models.Mdl.fromStore(dta_mdl)
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)

    if tsk.id: return noUpd, noUpd
    trgSrc = getTriggerId()


    if trgSrc == K.btnClean:
        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.clear
        mdl.msg = 'Start clearing all asset data'

    elif trgSrc == K.btnFetch:
        mdl.id = ks.pg.fetch
        mdl.cmd = ks.cmd.fetch.asset
        if now.usr:
            cnt = db.psql.count( now.usr.id )
            mdl.msg = f"Start getting assets[{cnt}] for user [{now.usr.name}] ?"
        # else:
        #     cnt = db.psql.count()
        #     mdl.msg = f"Start getting all users assets count[{cnt}] ?"

    return mdl.toStore(), nfy.toStore()


#------------------------------------------------------------------------
#------------------------------------------------------------------------



#========================================================================
# task acts
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

        # todo: add support for all users?

        db.pics.deleteForUsr(now.usr.id)

        onUpdate(10, "10%", f"Starting to fetch assets for {now.usr.name} from PostgreSQL")

        cntAll = db.psql.count(now.usr.id)
        if cntAll <= 0:
            msg = f"No assets found for {now.usr.name}"
            nfy.info(msg)
            return nfy, now, msg

        onUpdate(15, "15%", f"Found {cntAll} photos, starting to fetch assets")

        try:

            assets = db.psql.fetchAssets(now.usr, onUpdate=onUpdate)

        except Exception as e:
            msg = f"Error fetching assets for {now.usr.name}, {str(e)}"
            nfy.error(msg)
            return nfy, now, msg

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
task.mapFns[ks.cmd.fetch.asset] = onFetchAssets
task.mapFns[ks.cmd.fetch.clear] = onFetchClearAll
