import traceback
from typing import Optional

import db
from conf import ks, co
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd, ctx, ALL
from util import log
from mod import models, mapFns, IFnProg, taber

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.similar}',
    path_template=f'/{ks.pg.similar}/<assetId>',
    title=f"{ks.title}: " + ks.pg.similar.name,
)

class k:
    txtCntRs = 'sim-txt-cnt-records'
    txtCntOk = 'sim-txt-cnt-ok'
    txtCntNo = 'sim-txt-cnt-no'
    txtCntSel = 'sim-txt-cnt-sel'
    slideTh = "sim-inp-threshold"

    btnFind = "sim-btn-find"
    btnClear = "sim-btn-clear"
    btnDelChks = "sim-btn-delete-checkeds"

    tab = 'sim-taber'
    pager = "sim-pager"

    grid = "sim-grid"

    hisGv = 'sim-his-gv'


#========================================================================
def layout(assetId=None, **kwargs):
    # return flask.redirect('/target-page') #auth?


    if assetId:
        lg.info(f"[sim] from url assetId[{assetId}]")

        ass = db.pics.getById(assetId)
        if ass and db.dyn.dto.simId != assetId:
            db.dyn.dto.simId = assetId
            lg.info(f"[sim] =============>>>> set target assetId[{assetId}]")

    import ui
    return ui.renderBody([
        #====== top start =======================================================
        dbc.Row([
            dbc.Col(htm.H3(f"{ks.pg.similar.name}"), width=3),
            dbc.Col(htm.Small(f"{ks.pg.similar.desc}", className="text-muted"))
        ], className="mb-4"),


        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("System Similary Records"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(htm.Small("NotSearch", className="d-inline-block me-2"), width=6),
                            dbc.Col(dbc.Alert(f"0", id=k.txtCntNo, color="secondary", className="py-1 px-2 mb-2 text-center")),
                        ]),
                        dbc.Row([
                            dbc.Col(htm.Small("Pending", className="d-inline-block me-2"), width=6),
                            dbc.Col(dbc.Alert(f"0", id=k.txtCntRs, color="info", className="py-1 px-2 mb-2 text-center")),
                        ]),
                        dbc.Row([
                            dbc.Col(htm.Small("Resolved", className="d-inline-block me-2"), width=6),
                            dbc.Col(dbc.Alert(f"0", id=k.txtCntOk, color="success", className="py-1 px-2 mb-2 text-center")),
                        ]),
                        dbc.Row([htm.Small("Shows vectorized data in the local db and whether similarity comparison has been performed with other assets", className="text-muted")])
                    ])
                ], className="mb-4"),
            ], width=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Search Settings"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Similarity Threshold Range", className="txt-sm"),
                                dbc.Row([
                                    dbc.Col([
                                        dcc.RangeSlider(id=k.slideTh, min=0, max=1, step=0.01, marks=ks.defs.thMarks, value=[0.8, 0.99], className="mb-0"),
                                    ], className="mt-2"),
                                ])
                            ]),
                        ]),

                        dbc.Row([htm.Small("A threshold range sets both minimum and maximum similarity levels for matches. It helps you find things that are similar enough to what you want, without being too strict or too loose with your matching criteria. (Usually the default setting works just fine)", className="text-muted")])
                    ])
                ], className="mb-0"),


                dbc.Row([
                    dbc.Col([
                        dbc.Button("Find Similar", id=k.btnFind, color="primary", className="w-100", disabled=True),
                    ], width=8),

                    dbc.Col([
                        dbc.Button("Clear All Records", id=k.btnClear, color="danger", className="w-100", disabled=True),
                    ], width=4),
                ], className="mt-3"),

            ], width=8),
        ], className=""),

        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        #------------------------------------------------------------------------
        # Tabs
        #------------------------------------------------------------------------
        *taber.createTaber(
            tabId=k.tab,
            defs=[
                taber.Tab(title="current", active=True),
                taber.Tab(title="pending", disabled=True),
                "this is tab3"
            ],
            htmActs=[
                dbc.Button("delete checked (0)", id=k.btnDelChks, color="danger", size="md", className="w-60", disabled=True)
            ],
            tabBodies=[
                # Current tab content
                dbc.Spinner(
                    htm.Div(id=k.grid),
                    color="primary",
                    type="border",
                    spinner_style={"width": "3rem", "height": "3rem"},
                ),

                # Pending tab content
                htm.Div([
                    dbc.Row([
                        dbc.Col([
                            dbc.Spinner(
                                htm.Div(id=k.hisGv),
                                color="primary",
                                type="border",
                                spinner_style={"width": "3rem", "height": "3rem"},
                            ),
                        ], className="d-flex justify-content-center mb-3")
                    ], className="mt-2"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Pagination(id=k.pager, active_page=1, min_value=1, max_value=99, first_last=True, previous_next=True, fully_expanded=False, style={"display": ""})
                        ], className="d-flex justify-content-center mb-3")
                    ], className="mt-2"),
                ]),

                htm.Div([
                    htm.Span("這邊是tab3")
                ])
            ]
        ),

        #====== bottom end ======================================================
    ])


#========================================================================
# todo (think):
# - when select assets equal 2, display pair compare view?
#     card = gvs.create_pair_card(
#         photo1_id=pair["photo1_id"],
#         photo2_id=pair["photo2_id"],
#         similarity=pair["similarity"],
#         index=i + 1,
#         selected_images=selected_images
#     )
#========================================================================


#========================================================================
# callbacks
#========================================================================

# Register taber callback
taber.regCallbacks(k.tab)

#------------------------------------------------------------------------
# Update status counters
#------------------------------------------------------------------------
from ui import gridSimilar as gvs


#------------------------------------------------------------------------
# Sync taber state from now.pg.sim.taber
#------------------------------------------------------------------------
@callback(
    out(taber.id.store(k.tab), "data", allow_duplicate=True),
    inp(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sync_taber_from_now(dta_now):

    # lg.info( "[sync] from now" )

    if not dta_now or not dta_now['pg']:
        return dash.no_update

    taber = dta_now['pg']['sim']['taber']

    lg.info( f"[sync] from now, taber: {taber}" )
    return taber


#------------------------------------------------------------------------
# onStatus
#------------------------------------------------------------------------
@callback(
    [
        out(k.txtCntOk, "children"),
        out(k.txtCntRs, "children"),
        out(k.txtCntNo, "children"),
        out(k.btnFind, "disabled"),
        out(k.btnClear, "disabled"),
        out(k.grid, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp(ks.sto.now, "data"),
    [
        ste(ks.sto.nfy, "data"),
        ste(taber.id.store(k.tab), "data"),
    ],
    prevent_initial_call="initial_duplicate"
)
def similar_onStatus(dta_now, dta_nfy, dta_tar):

    now = models.Now.fromDict(dta_now)
    nfy = models.Nfy.fromDict(dta_nfy)
    tar = models.Taber.fromDict(dta_tar)

    # Store taber in page state
    now.pg.sim.taber = tar

    cntNo = db.pics.countSimOk(isOk=0)
    cntOk = db.pics.countSimOk(isOk=1)
    cntRs = db.pics.countHasSimIds()
    disFind = cntNo <= 0 or (cntRs >= cntNo)
    disCler = cntOk <= 0 and cntRs <= 0

    cntAssets = len(now.pg.sim.assets) if now.pg.sim.assets else -1

    lg.info(f"[sim:status] cntNo[{cntNo}] cntOk[{cntOk}] cntRs[{cntRs}] now.pg.sim.assets[{cntAssets}]")

    if cntAssets >= 1:
        #lg.info(f"[sim:status] assets: {now.pg.sim.assets[0]}")
        pass

    grid = []

    if cntNo <= 0:
        nfy.info("Not have any vectors, please do generate vectors first")

    grid = gvs.createGrid(now.pg.sim.assets, now.pg.sim.assId, onEmpty=[
        dbc.Alert("Please find the similar images..", color="secondary", className="text-center"),
    ])

    # Update pending tab (index 1) state based on cntRs
    if tar and len(tar.tabs) > 1:
        tab = tar.tabs[1]  # tab (pending)
        if tab:
            if cntRs >= 1:
                tab.disabled = False
                tab.title = f"pending ({cntRs})"
            else:
                tab.disabled = True
                tab.title = "pending"

            now.pg.sim.taber = tar


    return cntOk, cntRs, cntNo, disFind, disCler, grid, nfy.toDict(), now.toDict()



#------------------------------------------------------------------------
# Update status counters
#------------------------------------------------------------------------
@callback(
    out(ks.sto.now, "data"),
    inp({"type": "cbx-select", "id": ALL}, "value"),
    ste(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def update_selected_photos(clks, dta_now, dta_nfy):
    now = models.Now.fromDict(dta_now)
    nfy = models.Nfy.fromDict(dta_nfy)

    if ctx.triggered and now.pg.sim.assets and len(now.pg.sim.assets) > 1:
        trgId = ctx.triggered_id
        ass = next((a for a in now.pg.sim.assets if a.id == trgId.id), None)
        if ass:
            ass.selected = ctx.triggered[0]['value']
            # lg.info(f'[select] found: {ass.autoId}, selected: {ass.selected}, trgId: {trgId}')

    return now.toDict()


#========================================================================
# trigger modal
#========================================================================
@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    [
        inp(k.btnFind, "n_clicks"),
        inp(k.btnClear, "n_clicks"),
    ],
    [
        ste(k.slideTh, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def similar_RunModal(clk_fnd, clk_clr, thRange, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not clk_fnd and not clk_clr: return noUpd, noUpd, noUpd, noUpd

    trgId = getTriggerId()

    now = models.Now.fromDict(dta_now)
    mdl = models.Mdl.fromDict(dta_mdl)
    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)

    if tsk.id:
        # 檢查任務是否真的還在運行
        from mod.mgr.tskSvc import mgr
        if mgr and mgr.getInfo(tsk.id):
            task_info = mgr.getInfo(tsk.id)
            if task_info.status in ['pending', 'running']:
                lg.info(f"[similar] Task already running: {tsk.id}")
                return noUpd, noUpd, noUpd, noUpd

        # 如果任務已經完成或不存在，清除 tsk.id
        lg.info(f"[similar] Clearing completed task: {tsk.id}")
        tsk.id = None
        tsk.cmd = None

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    if trgId == k.btnClear:
        cntOk = db.pics.countSimOk(isOk=1)
        cntRs = db.pics.countHasSimIds()
        if cntOk <= 0 and cntRs <= 0:
            nfy.warn(f"[similar] DB does not contain any similarity records")
            return noUpd, nfy.toDict(), noUpd, noUpd

        mdl.reset()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.clear
        mdl.msg = [
            f"Are you sure you want to delete all records?", htm.Br(),
            f"include reslove({cntOk}) and resume({cntRs})", htm.Br(),
            htm.B("This operation cannot be undone"), htm.Br(),
            "You may need to perform all similarity searches again."
        ]

    # if trgId == k.btnResume:
    #     assets = db.pics.getAnySimPending()
    #     if assets:
    #         now.pg.sim.isContinued = True
    #         now.pg.sim.assId = assets[0].id
    #         now.pg.sim.assets = assets
    #         nfy.info(f"Loading pending groups, id[{now.pg.sim.assId}] with {len(assets)} similar images")


    elif trgId == k.btnFind:
        if now.cntVec <= 0:
            nfy.error("No vector data to process")
            now.pg.sim.reset()
            return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

        thMin, thMax = thRange
        thMin = co.valid.float(thMin, 0.80)
        thMax = co.valid.float(thMax, 0.99)

        asset: Optional[models.Asset] = None

        # if id from url
        if db.dyn.dto.simId:
            ass = db.pics.getById(db.dyn.dto.simId)
            if ass:
                if ass.simOk != 1:
                    lg.info(f"[sim] use selected asset id[{ass.id}]")
                    asset = ass
                else:
                    lg.warn(f"[sim] select asset simOk[{ass.simOk}] id[{ass.id}]")
            else:
                lg.warn(f"[sim] not found dst assetId[{db.dyn.dto.simId}]")

        # find from db
        if not asset:
            ass = db.pics.getAnyNonSim()
            if ass:
                asset = ass
                lg.info(f"[sim] found non-simOk assetId[{ass.id}]")

        now.pg.sim.reset()
        if not asset:
            nfy.warn(f"[sim] not any asset to find..")
        else:
            now.pg.sim.assId = asset.id

            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.find
            mdl.args = {'thMin': thMin, 'thMax': thMax}
            tsk = mdl.mkTsk()
            mdl.reset()
            # mdl.msg = [
            #     f"Begin finding similar?", htm.Br(),
            #     f"threshold[{thMin:.2f}-{thMax:.2f}]]",
            # ]
            return mdl.toDict(), nfy.toDict(), now.toDict(), tsk.toDict()

    lg.info(f"[similar] modal[{mdl.id}] cmd[{mdl.cmd}]")

    # 如果有清除過 tsk.id，需要更新 store
    return mdl.toDict(), nfy.toDict(), now.toDict(), tsk.toDict() if tsk.id is None else noUpd


#========================================================================
# task acts
#========================================================================
def sim_Clear(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    if tsk.id != ks.pg.similar:
        msg = f"[tsk] wrong triggerId[{tsk.id}]"
        lg.warn(msg)
        return nfy, now, msg

    try:
        onUpdate(10, "10%", "Preparing to clear similarity records...")

        cntOk = db.pics.countSimOk(isOk=1)
        cntRs = db.pics.countHasSimIds()

        if cntOk <= 0 and cntRs <= 0:
            msg = "No similarity records to clear"
            lg.info(msg)
            nfy.info(msg)
            return nfy, now, msg

        onUpdate(30, "30%", "Clearing similarity records from database...")

        db.pics.clearSimIds()

        onUpdate(90, "90%", "Updating dynamic data...")

        if hasattr(db.dyn.dto, 'simId'): db.dyn.dto.simId = None
        now.pg.sim.assets = []
        now.pg.sim.assId = None

        onUpdate(100, "100%", "Clear completed")

        msg = f"Successfully cleared {cntOk + cntRs} similarity records"
        lg.info(f"[sim_Clear] {msg}")
        nfy.success(msg)

        return nfy, now, msg

    except Exception as e:
        msg = f"Failed to clear similarity records: {str(e)}"
        lg.error(f"[sim_Clear] {msg}")
        lg.error(traceback.format_exc())
        nfy.error(msg)
        return nfy, now, msg


def sim_FindSimilar(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: IFnProg):
    if tsk.id != ks.pg.similar:
        msg = f"[tsk] wrong triggerId[{tsk.id}]"
        lg.warn(msg)
        return nfy, now, msg

    thMin, thMax = tsk.args.get("thMin", 0.80), tsk.args.get("thMax", 0.99)

    try:
        # todo: 如果資料只包含自已
        #   - 如果是無引導id, 應該自動尋找下一筆
        #   - 如果是有引導id, 告知找不到相似圖片就停止

        assetId = now.pg.sim.assId
        if not assetId: raise RuntimeError(f"[tsk] sim.assId is empty")

        onUpdate(1, "1%", f"prepare..")

        asset = db.pics.getById(assetId)

        if not asset:
            raise RuntimeError(f"[tsk] not found assetId[{assetId}]")

        onUpdate(5, "5%", f"Starting search with thresholds [{thMin:.2f}-{thMax:.2f}]")

        # less will contains self
        infos = db.vecs.findSimiliar(asset.id, thMin, thMax)

        asset.simInfos = infos

        for idx, info in enumerate(infos):
            if info.isSelf:
                lg.info(f"  no.{idx + 1}: ID[{info.id}] (self), score[{info.score:.6f}]")
            else:
                lg.info(f"  no.{idx + 1}: ID[{info.id}], score[{info.score:.6f}]")

        db.pics.setSimIds(asset.id, infos)

        simIds = [i.id for i in infos if not i.isSelf]
        doneIds = {asset.id}

        pgBse = 10.0
        pgMax = 90.0

        pgAll = len(simIds)
        if pgAll == 0:
            db.pics.setSimIds(asset.id, infos, isOk=0)

            now.pg.sim.reset()

            onUpdate(100, "100%", f"No similar photos found for {asset.originalFileName}")
            msg = f"No similar photos found for {asset.originalFileName}"
            nfy.info(msg)
            return nfy, now, msg

        cntDone = 0

        # looping find all childs
        while simIds:
            simId = simIds.pop(0)
            if simId in doneIds: continue

            doneIds.add(simId)
            cntDone += 1

            prog = pgBse + (pgMax - pgBse) * (cntDone / pgAll)
            prog = min(prog, pgMax)
            onUpdate(prog, f"{prog:.0f}%", f"Processing similar photo {cntDone}/{pgAll}")

            try:
                lg.info(f"[sim] search child id[{simId}]")
                cInfos = db.vecs.findSimiliar(simId, thMin, thMax)

                db.pics.setSimIds(simId, cInfos)

                ass = db.pics.getById(simId)

                for info in cInfos:
                    if not info.isSelf and info.id not in doneIds:
                        simIds.append(info.id)
                        pgAll += 1
            except Exception as ce:
                lg.warning(f"Error processing similar image {simId}: {ce}")
                continue

        onUpdate(95, "95%", f"Finalizing similar photo relationships")

        now.pg.sim.assId = asset.id
        now.pg.sim.assets = db.pics.getSimGroup(asset.id)

        onUpdate(100, "100%", f"Completed finding similar photos for {asset.originalFileName}")

        cntInfos = len(infos)
        cntAll = len(doneIds)
        msg = [f"Found {len(infos)} similar photos for {asset.originalFileName}"]

        if cntAll > cntInfos:
            msg.extend([htm.Br(), f"include ({cntAll - cntInfos}) asset extra tree in similar tree."])

        nfy.success(msg)

        return nfy, now, msg

    except Exception as e:
        msg = f"Similar photo search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.pg.sim.reset()
        return nfy, now, msg


#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.sim.find] = sim_FindSimilar
mapFns[ks.cmd.sim.clear] = sim_Clear
