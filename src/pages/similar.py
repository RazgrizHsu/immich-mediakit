import traceback
from typing import Optional

import core
import db
from conf import ks, co
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd, ctx, ALL
from util import log
from mod import mapFns
from ui import gvSim as gvs
from mod import models, tskSvc
from mod.models import Mdl, Now, Cnt, Nfy, Pager, Tsk
from ui import pager

lg = log.get(__name__)

# Debug flag for verbose logging
DEBUG = False

dash.register_page(
    __name__,
    path=f'/{ks.pg.similar}',
    path_template=f'/{ks.pg.similar}/<autoId>',
    title=f"{ks.title}: " + ks.pg.similar.name,
)

class k:
    assFromUrl = 'sim-AssFromUrl'

    txtCntRs = 'sim-txt-cnt-records'
    txtCntOk = 'sim-txt-cnt-ok'
    txtCntNo = 'sim-txt-cnt-no'
    txtCntSel = 'sim-txt-cnt-sel'
    slideTh = "sim-inp-threshold"

    btnFind = "sim-btn-find"
    btnClear = "sim-btn-clear"
    btnCbxRm = "sim-btn-CbxRm"
    btnCbxOk = "sim-btn-CbxOk"

    tabs = 'sim-tabs'
    pagerPnd = "sim-pager-pnd"

    gvSim = "sim-gvSim"
    gvPnd = 'sim-gvPnd'


#========================================================================
def layout(autoId=None, **kwargs):
    # return flask.redirect('/target-page') #auth?

    guideAss: Optional[models.Asset] = None

    if autoId:
        lg.info(f"[sim] from url autoId[{autoId}]")

        guideAss = db.pics.getByAutoId(autoId)
        if guideAss:
            lg.info(f"[sim] =============>>>> set target assetId[{guideAss.id}]")

    import ui
    return ui.renderBody([
        #====== top start =======================================================
        dcc.Store(id=k.assFromUrl, data=guideAss),

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
                                        dcc.RangeSlider(
                                            id=k.slideTh, min=0.5, max=1, step=0.01, marks=ks.defs.thMarks,
                                            value=[0.9, 1.0],
                                            tooltip={
                                                "placement": "top", "always_visible": True,
                                                "style": {"padding": "3px 5px 3px 5px", "fontSize": "15px"},
                                            },
                                            className="mb-0"
                                        ),
                                    ], className="mt-2"),
                                ])
                            ]),
                        ]),

                        dbc.Row([htm.Small("A threshold range sets both minimum and maximum similarity levels for matches. It helps you find things that are similar enough to what you want, without being too strict or too loose with your matching criteria. (Usually the default setting works just fine)", className="text-muted")])
                    ])
                ], className="mb-0"),


                dbc.Row([
                    dbc.Col([
                        dbc.Button(f"Find Similar", id=k.btnFind, color="primary", className="w-100", disabled=True),
                        htm.Br(),
                        htm.Small("No similar found → auto-mark resolved", className="ms-2 me-2")
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
        htm.Div([

            # Tabs
            dbc.Tabs(
                id=k.tabs,
                active_tab="tab-current",
                children=[
                    dbc.Tab(
                        label="current",
                        tab_id="tab-current",
                        children=[

                            # Action buttons
                            htm.Div([
                                dbc.Button("delete selected (0)", id=k.btnCbxRm, color="danger", size="sm", className="me-2", disabled=True),
                                dbc.Button("mark all resolved", id=k.btnCbxOk, color="success", size="sm", disabled=True)
                            ], className="mb-3 text-end"),


                            dbc.Spinner(
                                htm.Div(id=k.gvSim),
                                color="success",
                                type="border",
                                spinner_style={"width": "3rem", "height": "3rem"},
                            ),
                        ]
                    ),
                    dbc.Tab(
                        label="pending",
                        tab_id="tab-pending",
                        id="tab-pending",
                        disabled=True,
                        children=[
                            htm.Div([
                                # top pager
                                *pager.createPager(pgId=k.pagerPnd, idx=0, className="mb-3"),

                                # Grid view
                                dbc.Spinner(
                                    htm.Div(id=k.gvPnd),
                                    color="success",
                                    type="border",
                                    spinner_style={"width": "3rem", "height": "3rem"},
                                ),

                                # bottom pager
                                *pager.createPager(pgId=k.pagerPnd, idx=1, className="mt-3"),

                                # Main pager (store only)
                                *pager.createStore(pgId=k.pagerPnd, page=1, size=20, total=0),
                            ], className="text-center")
                        ]
                    )
                ]
            )
        ],
            className="ITab"
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

pager.regCallbacks(k.pagerPnd)


#------------------------------------------------------------------------
# Sync tab changes to now state
#------------------------------------------------------------------------
@callback(
    out(ks.sto.now, "data", allow_duplicate=True),
    inp(k.tabs, "active_tab", ),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_OnTabChange(active_tab, dta_now):
    if not active_tab or not dta_now: return noUpd

    now = Now.fromDict(dta_now)
    now.pg.sim.activeTab = active_tab

    # lg.info(f"[sim:tab] Tab changed to: {active_tab}")

    return now.toDict()

#------------------------------------------------------------------------
# Handle pager changes - reload pending data
#------------------------------------------------------------------------
@callback(
    [
        out(k.gvPnd, "children", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp(pager.id.store(k.pagerPnd), "data"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_onPagerChanged(dta_pgr, dta_now):
    if not dta_pgr or not dta_now: return noUpd, noUpd

    now = Now.fromDict(dta_now)
    pgr = Pager.fromDict(dta_pgr)

    # Check if we're already on this page with same data
    oldPgr = now.pg.sim.pagerPnd
    if oldPgr and oldPgr.idx == pgr.idx and oldPgr.size == pgr.size and oldPgr.cnt == pgr.cnt:
        if DEBUG: lg.info(f"[sim:pager] Already on page {pgr.idx}, skipping reload")
        return noUpd, noUpd

    now.pg.sim.pagerPnd = pgr

    paged = db.pics.getPendingPaged(page=pgr.idx, size=pgr.size)
    now.pg.sim.assPend = paged

    lg.info(f"[sim:pager] paged: {pgr.idx}/{(pgr.cnt + pgr.size - 1) // pgr.size}, got {len(paged)} items")

    gvPnd = gvs.mkPndGrid(now.pg.sim.assPend, onEmpty=[
        dbc.Alert("No pending items on this page", color="secondary", className="text-center"),
    ])

    return gvPnd, now.toDict()

# The pager initialization is now handled by regCallbacks with secondaryIds


#------------------------------------------------------------------------
# assert from url
#------------------------------------------------------------------------
@callback(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    inp(k.assFromUrl, "data"),
    [
        ste(ks.sto.now, "data"),
        ste(k.slideTh, "value"),
    ],
    prevent_initial_call=True
)
def sim_SyncUrlAssetToNow(dta_ass, dta_now, thVals):
    if not dta_ass:
        return noUpd, noUpd

    now = Now.fromDict(dta_now)
    ass = models.Asset.fromDict(dta_ass)

    lg.info(f"[sim:sync] asset from url: #{ass.autoId} id[{ass.id}]")

    now.pg.sim.assFromUrl = ass
    now.pg.sim.assId = ass.id

    thMin, thMax = thVals

    tsk = Tsk()
    tsk.id = ks.pg.similar
    tsk.cmd = ks.cmd.sim.find
    tsk.name = f'Find similar for #{ass.autoId}'
    tsk.msg = f'Search images similar to {ass.originalFileName} with threshold [{thMin:.2f} - {thMax:.2f}]'
    tsk.args = {'thMin': thMin, 'thMax': thMax, 'fromUrl': True}

    return now.toDict(), tsk.toDict()


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
        out(k.btnCbxOk, "disabled"),
        out(k.gvSim, "children"),
        out(k.gvPnd, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(pager.id.store(k.pagerPnd), "data", allow_duplicate=True),
        out("tab-pending", "disabled"),
        out("tab-pending", "label"),
        out(k.tabs, "active_tab", allow_duplicate=True),
    ],
    inp(ks.sto.now, "data"),
    [
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call="initial_duplicate"
)
def sim_Load(dta_now, dta_nfy):
    now = Now.fromDict(dta_now)
    nfy = Nfy.fromDict(dta_nfy)

    trgId = getTriggerId()

    cntNo = db.pics.countSimOk(isOk=0)
    cntOk = db.pics.countSimOk(isOk=1)
    cntPn = db.pics.countSimPending()

    # Disable Find button if task is running
    from mod.mgr.tskSvc import mgr
    isTaskRunning = False
    if mgr:
        for tskId, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                lg.info(f"[sim:load] Running task found: {tskId}, status: {info.status.value}")
                isTaskRunning = True
                break

    disFind = cntNo <= 0 or (cntPn >= cntNo) or isTaskRunning
    disCler = cntOk <= 0 and cntPn <= 0

    cntAssets = len(now.pg.sim.assCur) if now.pg.sim.assCur else -1
    disOk = cntAssets <= 0

    if cntAssets >= 1:
        #lg.info(f"[sim:load] assets: {now.pg.sim.assets[0]}")
        pass

    gvSim = []

    if cntNo <= 0:
        nfy.info("Not have any vectors, please do generate vectors first")

    # todo: 動態獲取關聯群組
    # relatedGroups = []
    # if now.pg.sim.assId:
    #     asset = db.pics.getById(now.pg.sim.assId)
    #     if asset and hasattr(asset, 'simGID') and asset.simGID:
    #         # 找出所有相同群組的其他代表
    #         relatedAssets = db.pics.getAssetsByGID(asset.simGID)
    #
    #         # 對每個關聯群組獲取其完整的相似照片群組
    #         for ra in relatedAssets:
    #             if ra.id != now.pg.sim.assId:
    #                 # 獲取這個群組的所有相似照片
    #                 groupAssets = db.pics.getSimGroup(ra.id)
    #                 if groupAssets:
    #                     # 將群組資訊存儲在第一個元素（主圖）中
    #                     ra.groupAssets = groupAssets
    #                     relatedGroups.append(ra)

    gvSim = gvs.mkGrid(now.pg.sim.assCur, now.pg.sim.assId, onEmpty=[
        dbc.Alert("Please find the similar images..", color="secondary", className="text-center m-5"),
    ])

    # Initialize or get pager
    pgr = now.pg.sim.pagerPnd if now.pg.sim.pagerPnd else Pager(idx=1, size=20)

    # Update pager total count
    pagerData = None
    oldPn = pgr.cnt
    if pgr.cnt != cntPn:
        pgr.cnt = cntPn
        # Keep current page if still valid, otherwise reset to last valid page
        totalPages = (cntPn + pgr.size - 1) // pgr.size if cntPn > 0 else 1
        if pgr.idx > totalPages:
            pgr.idx = max(1, totalPages)
        now.pg.sim.pagerPnd = pgr
        # Only update pager store if count actually changed
        if oldPn != cntPn: pagerData = pgr

    lg.info(f"--------------------------------------------------------------------------------")
    lg.info(f"[sim:load] cntNo[{cntNo}] cntOk[{cntOk}] cntPn[{cntPn}]({oldPn}) now[{cntAssets}] assId[{now.pg.sim.assId}]")
    # lg.info(f"[sim:load] tgId[{trgId}] assId[{now.pg.sim.assId}] assCur[{len(now.pg.sim.assCur)}] assPend[{len(now.pg.sim.assPend)}]")

    # Load pending data - reload if count changed or no data
    needReload = False
    if cntPn > 0:
        if not now.pg.sim.assPend or len(now.pg.sim.assPend) == 0:
            needReload = True
        elif oldPn != cntPn:
            needReload = True
            lg.info(f"[sim:load] Pending count changed from {oldPn} to {cntPn}, reloading data")

    if needReload:
        paged = db.pics.getPendingPaged(page=pgr.idx, size=pgr.size)
        lg.info(f"[sim:load] pend reload, idx[{pgr.idx}] size[{pgr.size}] got[{len(paged)}]")
        now.pg.sim.assPend = paged

    gvPnd = gvs.mkPndGrid(now.pg.sim.assPend, onEmpty=[
        dbc.Alert("Please find the similar images..", color="secondary", className="text-center m-5"),
    ])

    # Update pending tab state based on cntPn
    tabDisabled = cntPn < 1
    tabLabel = f"pending ({cntPn})" if cntPn >= 1 else "pending"

    nowDict = now.toDict()

    activeTab = now.pg.sim.activeTab if now.pg.sim.activeTab else "tab-current"

    return cntOk, cntPn, cntNo, disFind, disCler, disOk, gvSim, gvPnd, nfy.toDict(), nowDict, pagerData.toDict() if pagerData else noUpd, tabDisabled, tabLabel, activeTab


#------------------------------------------------------------------------
# Update status counters
#------------------------------------------------------------------------
@callback(
    out(ks.sto.now, "data"),
    [
        inp({"type": "card-select", "id": ALL}, "n_clicks"),
    ],
    ste(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def sim_OnSelectAsset(clks_crd, dta_now, dta_nfy):
    hasClk = any(clks_crd)
    if not hasClk: return noUpd

    lg.info(f"[sim:select] any[{hasClk}] {clks_crd}")

    now = Now.fromDict(dta_now)
    nfy = Nfy.fromDict(dta_nfy)

    selected = []

    if ctx.triggered and now.pg.sim.assCur:
        trgId = ctx.triggered_id

        tid = trgId['id']
        # lg.info(f"[sim:select] selected[{tid}]")

        for ass in now.pg.sim.assCur:
            if ass.id == tid:
                ass.selected = not ass.selected
                lg.info(f'[header-click] toggled: {ass.autoId}, selected: {ass.selected}')

            if ass.selected:
                selected.append(ass)

    lg.info(f'[sim:select] Selected: {len(selected)}/{len(now.pg.sim.assCur)}')
    now.pg.sim.assSelect = selected

    return now.toDict()


#------------------------------------------------------------------------
# Update button state based on selections
#------------------------------------------------------------------------
@callback(
    [
        out(k.btnCbxRm, "children"),
        out(k.btnCbxRm, "disabled"),
    ],
    inp(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_OnNowChangeSelects(dta_now):
    now = Now.fromDict(dta_now)

    selCnt = len(now.pg.sim.assSelect)

    # if selCnt: lg.info(f"[sim:slect] selCnt[{selCnt}]")

    btnText = f"delete selected ( {selCnt} )"
    btnDisabled = selCnt == 0

    return btnText, btnDisabled


#------------------------------------------------------------------------
# Handle group view button click
#------------------------------------------------------------------------
@callback(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
        out(k.tabs, "active_tab", allow_duplicate=True),  # Switch to current tab
    ],
    inp({"type": "btn-view-group", "id": ALL}, "n_clicks"),
    [
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call=True
)
def sim_OnSwitchViewGroup(clks, dta_now):
    if not ctx.triggered: return noUpd, noUpd

    # Check if any button was actually clicked
    if not any(clks): return noUpd, noUpd

    now = Now.fromDict(dta_now)

    trgId = ctx.triggered_id
    assId = trgId["id"]

    # lg.info(f"[sim:view-group] switch: id[{assId}] clks[{clks}]")

    now.pg.sim.assId = assId
    now.pg.sim.assCur = db.pics.getSimGroup(assId)
    now.pg.sim.assSelect = []

    if DEBUG: lg.info(f"[sim:view-group] Loaded {len(now.pg.sim.assCur)} assets for group")

    return now.toDict(), "tab-current"  # Switch to current tab


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
        inp(k.btnCbxRm, "n_clicks"),
        inp(k.btnCbxOk, "n_clicks"),
    ],
    [
        ste(k.slideTh, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.cnt, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def sim_RunModal(clk_fnd, clk_clr, clk_dse, clk_rse, thRange, dta_now, dta_cnt, dta_mdl, dta_tsk, dta_nfy):
    if not clk_fnd and not clk_clr and not clk_dse and not clk_rse: return noUpd, noUpd, noUpd, noUpd

    trgId = getTriggerId()

    now = Now.fromDict(dta_now)
    cnt = Cnt.fromDict(dta_cnt)
    mdl = Mdl.fromDict(dta_mdl)
    tsk = Tsk.fromDict(dta_tsk)
    nfy = Nfy.fromDict(dta_nfy)

    # Check if any task is already running
    from mod.mgr.tskSvc import mgr
    if mgr:
        for tid, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                nfy.warn(f"Task already running, please wait for it to complete")
                return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

    if tsk.id:
        if mgr and mgr.getInfo(tsk.id):
            ti = mgr.getInfo(tsk.id)
            if ti.status in ['pending', 'running']:
                nfy.warn(f"[similar] Task already running: {tsk.id}")
                return noUpd, noUpd, noUpd, noUpd
            # lg.info(f"[similar] Clearing completed task: {tsk.id}")
            tsk.id = None
            tsk.cmd = None

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    #------------------------------------------------------------------------
    if trgId == k.btnCbxOk:
        ass = now.pg.sim.assCur
        cnt = len(ass)

        lg.info(f"[sim:reslove] {cnt} assets")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.selsOk
            mdl.msg = f"Are you sure mark resloved current images( {cnt} )?"

            mdl.assets = ass
    #------------------------------------------------------------------------
    if trgId == k.btnCbxRm:
        ass = now.pg.sim.assSelect
        cnt = len(ass)

        lg.info(f"[sim:delSels] {cnt} assets selected")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.selsRm
            mdl.msg = [
                f"Are you sure you want to Delete select images( {cnt} )?", htm.Br(),
                htm.B("This operation cannot be undone"),
            ]
            mdl.assets = ass

    #------------------------------------------------------------------------
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

    #------------------------------------------------------------------------
    elif trgId == k.btnFind:
        if cnt.vec <= 0:
            nfy.error("No vector data to process")
            now.pg.sim.clearAll()
            return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

        thMin, thMax = thRange
        thMin = co.valid.float(thMin, 0.80)
        thMax = co.valid.float(thMax, 0.99)

        asset: Optional[models.Asset] = None

        # asset from url
        isFromUrl = False
        if now.pg.sim.assFromUrl:
            ass = now.pg.sim.assFromUrl  #consider read from db again?
            if ass:
                if ass.simOk != 1:
                    lg.info(f"[sim] use selected asset id[{ass.id}]")
                    asset = ass
                    isFromUrl = True
                else:
                    nfy.info(f"[sim] the asset #{ass.autoId} already resolved")
                    now.pg.sim.assFromUrl = None
                    return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd
            else:
                nfy.warn(f"[sim] not found dst assetId[{now.pg.sim.assFromUrl}]")
                now.pg.sim.assFromUrl = None
                return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

        # find from db
        if not asset:
            ass = db.pics.getAnyNonSim()
            if ass:
                asset = ass
                lg.info(f"[sim] found non-simOk assetId[{ass.id}]")

        if not isFromUrl:
            now.pg.sim.clearAll()
        if not asset:
            nfy.warn(f"[sim] not any asset to find..")
        else:
            now.pg.sim.assId = asset.id

            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.find
            mdl.args = {'thMin': thMin, 'thMax': thMax, 'fromUrl': isFromUrl}
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
from mod.models import IFnProg

def sim_Clear(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt

    try:
        doReport(10, "Preparing to clear similarity records...")

        cntOk = db.pics.countSimOk(isOk=1)
        cntRs = db.pics.countHasSimIds()

        if cntOk <= 0 and cntRs <= 0:
            msg = "No similarity records to clear"
            lg.info(msg)
            nfy.info(msg)
            return nfy, now, msg

        doReport(30, "Clearing similarity records from database...")

        db.pics.clearAllSimIds()

        doReport(90, "Updating dynamic data...")

        now.pg.sim.assFromUrl = None

        now.pg.sim.clearAll()

        doReport(100, "Clear completed")

        msg = f"Successfully cleared {cntOk + cntRs} similarity records"
        lg.info(f"[sim_Clear] {msg}")
        nfy.success(msg)

        return sto, msg

    except Exception as e:
        msg = f"Failed to clear similarity records: {str(e)}"
        lg.error(f"[sim_Clear] {msg}")
        lg.error(traceback.format_exc())
        nfy.error(msg)
        raise RuntimeError(msg)


def sim_FindSimilar(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt, tsk = sto.nfy, sto.now, sto.cnt, sto.tsk

    thMin, thMax, isFromUrl = tsk.args.get("thMin", 0.80), tsk.args.get("thMax", 0.99), tsk.args.get("fromUrl", False)

    # 如果是從 URL 進入，清除引導避免重複搜尋
    if isFromUrl and now.pg.sim.assFromUrl:
        lg.info(f"[sim] Clearing URL guidance for asset {now.pg.sim.assFromUrl.autoId if now.pg.sim.assFromUrl else 'unknown'}")
        now.pg.sim.assFromUrl = None

    try:
        assetId = now.pg.sim.assId
        if not assetId: raise RuntimeError(f"[tsk] sim.assId is empty")

        doReport(1, f"prepare..")

        asset = db.pics.getById(assetId)

        if not asset:
            raise RuntimeError(f"[tsk] not found assetId[{assetId}]")

        processedCount = 0
        while True:
            progressMsg = f"Searching for #{asset.autoId}, thresholds[{thMin:.2f}-{thMax:.2f}]"
            if processedCount > 0:
                progressMsg = f"No similar found for {processedCount} assets, now searching #{asset.autoId}"
            doReport(10, progressMsg)

            # less will contains self
            infos = db.vecs.findSimiliar(asset.id, thMin, thMax)

            asset.simInfos = infos

            for idx, inf in enumerate(infos):
                if inf.isSelf:
                    lg.info(f"  no.{idx + 1}: ID[{inf.id}] (self), score[{inf.score:.6f}]")
                else:
                    lg.info(f"  no.{idx + 1}: ID[{inf.id}], score[{inf.score:.6f}]")

            import time
            time.sleep(0.1)
            db.pics.setSimIds(asset.id, infos)

            simIds = [i.id for i in infos if not i.isSelf]
            doneIds = {asset.id}

            pgBse = 10.0
            pgMax = 90.0

            pgAll = len(simIds)
            if pgAll == 0:
                lg.info(f"[sim] NoFound #{asset.autoId}")
                time.sleep(0.1)
                db.pics.setSimIds(asset.id, infos, isOk=1)
                processedCount += 1

                #如果是無引導id, 應該自動尋找下一筆
                if not isFromUrl:
                    nextAss = db.pics.getAnyNonSim()
                    if nextAss:
                        lg.info(f"[sim] Next: #{nextAss.autoId}")
                        asset = nextAss
                        assetId = nextAss.id
                        now.pg.sim.assId = nextAss.id
                        doReport(5, f"No similar found for #{asset.autoId - 1}, continuing to #{asset.autoId}...")
                        continue
                else:
                    lg.info(f"[sim] break bcoz from url")

                doReport(100, f"NoFound #{asset.autoId}")
                msg = f"No similar photos found for {asset.autoId}"
                if processedCount > 1:
                    msg = f"Processed {processedCount} assets without similar. Last: #{asset.autoId}"
                nfy.info(msg)
                return nfy, now, msg

            # 找到有相似圖片的，跳出迴圈繼續處理
            break

        cntDone = 0

        # looping find all childs
        while simIds:
            simId = simIds.pop(0)
            if simId in doneIds: continue

            doneIds.add(simId)
            cntDone += 1

            prog = pgBse + (pgMax - pgBse) * (cntDone / pgAll)
            prog = min(prog, pgMax)
            doReport(prog, f"Processing similar photo {cntDone}/{pgAll}")

            try:
                lg.info(f"[sim] search child id[{simId}]")
                cInfos = db.vecs.findSimiliar(simId, thMin, thMax)

                db.pics.setSimIds(simId, cInfos)

                ass = db.pics.getById(simId)

                for inf in cInfos:
                    if not inf.isSelf and inf.id not in doneIds:
                        simIds.append(inf.id)
                        pgAll += 1
            except Exception as ce:
                raise RuntimeError(f"Error processing similar image {simId}: {ce}")

        # auto mark
        db.pics.setSimAutoMark()

        doReport(95, f"Finalizing similar photo relationships")

        now.pg.sim.assId = asset.id
        now.pg.sim.assCur = db.pics.getSimGroup(asset.id)
        now.pg.sim.assSelect = []
        now.pg.sim.activeTab = "tab-current"

        lg.info(f"[sim] done, asset #{asset.autoId}")

        if not now.pg.sim.assCur:
            raise RuntimeError(f"the get SimGroup not found by asset.id[{asset.id}]")

        doReport(100, f"Completed finding similar photos for #{asset.autoId}")

        cntInfos = len(infos)
        cntAll = len(doneIds)
        msg = [f"Found {len(infos)} similar photos for #{asset.autoId}"]

        if cntAll > cntInfos:
            msg.append(f"include ({cntAll - cntInfos}) asset extra tree in similar tree.")

        if processedCount > 1:
            msg.append(f"Auto-processed {processedCount} assets before finding similar photos.")

        nfy.success(msg)

        return sto, msg

    except Exception as e:
        msg = f"[sim] Similar search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.pg.sim.clearAll()
        raise RuntimeError(msg)


def sim_DelSelected(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assAlls = now.pg.sim.assCur
        assSels = now.pg.sim.assSelect
        assLefts = [a for a in assAlls if a.autoId not in {s.autoId for s in assSels}]

        cntSelect = len(assSels)
        msg = f"[sim] Delete Selected Assets( {cntSelect} ) Success!"

        if not assSels or cntSelect == 0: raise RuntimeError("Selected not found")

        ids = [a.id for a in assSels]

        for a in assSels:
            lg.info(f"[sim:delSelects] delete asset #[{a.autoId}] Id[ {a.id} ]")

        # immich
        core.trashBy(ids)

        #清除同個simGID的相似資料讓他重新找
        db.pics.setResloveBy(assSels, 0)

        now.pg.sim.clearNow()
        now.pg.sim.activeTab = "tab-pending"

        cnt.refreshFromDB()

        nfy.success(msg)

        return sto, msg
    except Exception as e:
        msg = f"[sim] Delete selected failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.pg.sim.clearAll()

        raise RuntimeError(msg)


def sim_ResloveAll(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assets = now.pg.sim.assCur
        cntAll = len(assets)
        msg = f"[sim] set Resloved Assets( {cntAll} ) Success!"

        if not assets or cnt == 0: raise RuntimeError("Current Assets not found")

        db.pics.setResloveBy(assets)

        now.pg.sim.clearNow()

        nfy.success(msg)

        # update cnts
        cnt.refreshFromDB()

        return sto, msg
    except Exception as e:
        msg = f"[sim] Delete selected failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.pg.sim.clearNow()

        raise RuntimeError(msg)

#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.sim.find] = sim_FindSimilar
mapFns[ks.cmd.sim.clear] = sim_Clear
mapFns[ks.cmd.sim.selsOk] = sim_ResloveAll
mapFns[ks.cmd.sim.selsRm] = sim_DelSelected
