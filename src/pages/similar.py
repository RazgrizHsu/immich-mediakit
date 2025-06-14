import traceback
from typing import Optional
import time

import immich
import db
from conf import ks, co
from dsh import dash, htm, dcc, dbc, inp, out, ste, getTrgId, noUpd, ctx, ALL, Patch
from dsh import cbk, ccbk, cbkFn
from util import log
from mod import mapFns, models, tskSvc
from mod.models import Mdl, Now, Cnt, Nfy, Pager, Tsk, Ste
from ui import pager, cardSets, gvSim as gvs


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

    btnAllSelect = 'sim-btn-AllSelect'
    btnAllCancel = 'sim-btn-AllCancel'

    btnFind = "sim-btn-fnd"
    btnClear = "sim-btn-clear"
    btnReset = "sim-btn-reset"
    btnRmSel = "sim-btn-RmSel"
    btnOkSel = "sim-btn-OkSel"
    btnOkAll = "sim-btn-OkAll"
    btnRmAll = "sim-btn-RmAll"
    cbxNChkOkAll = "sim-cbx-NChk-OkAll"
    cbxNChkRmSel = "sim-cbx-NChk-RmSel"
    cbxNChkOkSel = "sim-cbx-NChk-OkSel"
    cbxNChkRmAll = "sim-cbx-NChk-RmAll"


    tabs = 'sim-tabs'
    tabCur = "tab-current"
    tabPnd = "tab-pend"
    pagerPnd = "sim-pager-pnd"

    gvSim = "sim-gvSim"
    gvPnd = 'sim-gvPnd'


#========================================================================
def layout(autoId=None):
    # return flask.redirect('/target-page') #auth?

    guideAss: Optional[models.Asset] = None

    if autoId:
        lg.info(f"[sim] from url autoId[{autoId}]")
        try:

            guideAss = db.pics.getByAutoId(autoId)
            if guideAss:
                lg.info(f"[sim] =============>>>> set target assetId[{guideAss.id}]")
        except:
            lg.error(f"[sim] not found asset from aid[{autoId}]", exc_info=True)

    import ui
    return ui.renderBody([
        #====== top start =======================================================
        dcc.Store(id=k.assFromUrl, data=guideAss.toDict() if guideAss else {}),

        # 客戶端選擇狀態管理的 dummy 元素
        htm.Div(id={"type": "dummy-output", "id": "selection"}, style={"display": "none"}),
        htm.Div(id={"type": "dummy-output", "id": "init-selection"}, style={"display": "none"}),

        htm.Div([
            htm.H3(f"{ks.pg.similar.name}"),
            htm.Small(f"{ks.pg.similar.desc}", className="text-muted")
        ], className="body-header"),


        dbc.Row([
            dbc.Col([
                #------------------------------------------------------------------------
                cardSets.renderThreshold(),
                cardSets.renderAutoSelect(),
                #------------------------------------------------------------------------
            ], width=4),

            dbc.Col([

                cardSets.renderCard(),

                dbc.Row([
                    dbc.Col([
                        dbc.Button(f"Find Similar", id=k.btnFind, color="primary", className="w-100", disabled=True),
                        htm.Br(),
                        htm.Small("No similar found → auto-mark resolved", className="ms-2 me-2")
                    ], width=6),

                    dbc.Col([
                        dbc.Button("Clear Search record but keep resloved", id=k.btnClear, color="danger me-1", className="w-100 mb-1", disabled=True),
                        dbc.Button("Reset Search records", id=k.btnReset, color="danger", className="w-58", disabled=True),
                    ], width=6, className="text-end"),
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

            dbc.Tabs(
                id=k.tabs,
                active_tab=k.tabCur,
                children=[
                    dbc.Tab(
                        label="current", tab_id=k.tabCur,
                        children=[

                            # Action buttons
                            htm.Div([

                                htm.Div([

                                    dbc.Button( [ htm.Span( className="fake-checkbox checked" ), "select All"], id=k.btnAllSelect, size="sm", color="secondary", disabled=True ),
                                    dbc.Button( [ htm.Span( className="fake-checkbox" ),"Deselect All"], id=k.btnAllCancel, size="sm", color="secondary", disabled=True ),

                                ], className="left"),


                                htm.Div([

                                    htm.Div([
                                        dbc.Button("Keep Select, Delete others", id=k.btnOkSel, color="success", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNChkOkSel, label="No-Confirm", className="sm")
                                    ]),

                                    htm.Div([
                                        dbc.Button("Del Select, Keep others", id=k.btnRmSel, color="danger", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNChkRmSel, label="No-Confirm", className="sm"),
                                    ]),

                                    htm.Div([
                                        dbc.Button("✅ Keep All", id=k.btnOkAll, color="success", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNChkOkAll, label="No-Confirm", className="sm")
                                    ]),

                                    htm.Div([
                                        dbc.Button("❌ Delete All", id=k.btnRmAll, color="danger", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNChkRmAll, label="No-Confirm", className="sm")
                                    ]),

                                ], className="right"),


                            ],
                                className="tab-acts"
                            ),


                            dbc.Spinner(
                                htm.Div(id=k.gvSim),
                                color="success", type="border", spinner_style={"width": "3rem", "height": "3rem"},
                            ),

                            # Floating Goto Top Button
                            htm.Button(
                                "↑ Top",
                                id="sim-goto-top-btn",
                                className="goto-top-btn",
                                style={"display": ""}
                            ),
                        ]
                    ),
                    dbc.Tab(
                        label="pending",
                        tab_id=k.tabPnd,
                        id=k.tabPnd,
                        disabled=True,
                        children=[
                            htm.Div([
                                # top pager
                                *pager.createPager(pgId=k.pagerPnd, idx=0, btnSize=9, className="mb-3"),

                                dbc.Spinner(
                                htm.Div(id=k.gvPnd),
                                color="success", type="border", spinner_style={"width": "3rem", "height": "3rem"},
                                ),

                                # bottom pager
                                *pager.createPager(pgId=k.pagerPnd, idx=1, btnSize=9, className="mt-3"),

                                # Main pager (store only)
                                *pager.createStore(pgId=k.pagerPnd),
                            ], className="text-center")
                        ]
                    ),
                ]
            )
        ],
            className="ITab"
        ),

        #====== bottom end ======================================================
    ])



#========================================================================
# callbacks
#========================================================================

pager.regCallbacks(k.pagerPnd)


#------------------------------------------------------------------------
# Sync tab changes to now state
#------------------------------------------------------------------------
@cbk(
    out(ks.sto.now, "data", allow_duplicate=True),
    inp(k.tabs, "active_tab", ),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_OnTabChange(active_tab, dta_now):
    if not active_tab or not dta_now: return noUpd

    now = Now.fromDict(dta_now)

    if now.sim.activeTab == active_tab: return noUpd

    lg.info(f"[sim:tab] Tab changed to: {active_tab} (from: {now.sim.activeTab})")

    patch = dash.Patch()
    patch['sim']['activeTab'] = active_tab
    return patch



#------------------------------------------------------------------------
# Handle pager changes - reload pending data
#------------------------------------------------------------------------
@cbk(
    [
        out(k.gvPnd, "children", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp(pager.id.store(k.pagerPnd), "data"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_onPagerChanged(dta_pgr, dta_now):
    if not dta_pgr or not dta_now: return noUpd.by(2)

    now = Now.fromDict(dta_now)
    pgr = Pager.fromDict(dta_pgr)

    # Check if we're already on this page with same data
    oldPgr = now.sim.pagerPnd
    if oldPgr and oldPgr.idx == pgr.idx and oldPgr.size == pgr.size and oldPgr.cnt == pgr.cnt:
        if DEBUG: lg.info(f"[sim:pager] Already on page {pgr.idx}, skipping reload")
        return noUpd.by(2)

    now.sim.pagerPnd = pgr

    paged = db.pics.getPagedPending(page=pgr.idx, size=pgr.size)
    now.sim.assPend = paged

    lg.info(f"[sim:pager] paged: {pgr.idx}/{(pgr.cnt + pgr.size - 1) // pgr.size}, got {len(paged)} items")

    gvPnd = gvs.mkPndGrid(now.sim.assPend, onEmpty=[
        dbc.Alert("No pending items on this page", color="secondary", className="text-center"),
    ])

    return gvPnd, now.toDict()



#------------------------------------------------------------------------
# assert from url
#------------------------------------------------------------------------
@cbk(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    inp(k.assFromUrl, "data"),
    [
        ste(ks.sto.now, "data"),
    ],
    prevent_initial_call="initial_duplicate"
)
def sim_SyncUrlAssetToNow(dta_ass, dta_now):
    now = Now.fromDict(dta_now)

    if not dta_ass:
        if not now.sim.assFromUrl: return noUpd.by(2)

        patch = dash.Patch()
        patch['sim']['assFromUrl'] = None
        return patch, noUpd

    ass = models.Asset.fromDict(dta_ass)

    lg.info(f"[sim:sync] asset from url: #{ass.autoId} id[{ass.id}]")

    now.sim.assFromUrl = ass
    now.sim.assAid = ass.autoId

    mdl = Mdl()
    mdl.id = ks.pg.similar
    mdl.cmd = ks.cmd.sim.fnd
    mdl.msg = f'Search images similar to {ass.autoId}'

    tsk = mdl.mkTsk()

    lg.info(f"[sim:sync] to task: {tsk}")

    return now.toDict(), tsk.toDict()


#------------------------------------------------------------------------
# onStatus
#------------------------------------------------------------------------
@cbk(
    [
        out(k.gvSim, "children"),
        out(k.gvPnd, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(pager.id.store(k.pagerPnd), "data", allow_duplicate=True),
        out(k.tabPnd, "disabled"),
        out(k.tabPnd, "label"),
        out(k.tabs, "active_tab", allow_duplicate=True),
    ],
    inp(ks.sto.now, "data"),
    [
        ste(ks.sto.nfy, "data"),
        ste(ks.sto.cnt, "data"),
    ],
    prevent_initial_call="initial_duplicate"
)
def sim_Load(dta_now, dta_nfy, dta_cnt):
    now = Now.fromDict(dta_now)
    nfy = Nfy.fromDict(dta_nfy)
    cnt = Cnt.fromDict(dta_cnt)

    trgId = getTrgId()
    if trgId: lg.info(f"[sim:load] load, trig: [ {trgId} ]")

    cntNo, cntOk, cntPn = cnt.simNo, cnt.simOk, cnt.simPnd

    gvSim = []

    if cntNo <= 0:
        nfy.info("Not have any vectors, please do generate vectors first")


    # Check condition group mode from dto settings
    if db.dto.simCondGrpMode:
        gvSim = gvs.mkGroupGrid(now.sim.assCur, onEmpty=[
            dbc.Alert("No grouped results found..", color="secondary", className="text-center m-5"),
        ])
    else:
        gvSim = gvs.mkGrid(now.sim.assCur, onEmpty=[
            dbc.Alert("Please find the similar images..", color="secondary", className="text-center m-5"),
        ])

    # Initialize or get pager
    pgr = now.sim.pagerPnd
    if not pgr:
        pgr = Pager(idx=1, size=20)
        now.sim.pagerPnd = pgr

    # Update pager total count
    pagerData = None
    oldPn = pgr.cnt
    if pgr.cnt != cntPn:
        pgr.cnt = cntPn
        # Keep current page if still valid, otherwise reset to last valid page
        totalPages = (cntPn + pgr.size - 1) // pgr.size if cntPn > 0 else 1
        if pgr.idx > totalPages: pgr.idx = max(1, totalPages)
        now.sim.pagerPnd = pgr
        # Only update pager store if count actually changed
        if oldPn != cntPn: pagerData = pgr

    lg.info(f"--------------------------------------------------------------------------------")
    lg.info(f"[sim:load] trig[{trgId}] condGrp[{db.dto.simCondGrpMode}] cntNo[{cntNo}] cntOk[{cntOk}] cntPn[{cntPn}]({oldPn}) assCur[{len(now.sim.assCur)}] assAid[{now.sim.assAid}]")

    # Load pending data - reload if count changed or no data
    needReload = False
    if cntPn > 0:
        if not now.sim.assPend or len(now.sim.assPend) == 0:
            needReload = True
        elif oldPn != cntPn:
            needReload = True
            lg.info(f"[sim:load] Pending count changed from {oldPn} to {cntPn}, reloading data")
    else:
        needReload = True

    if needReload:
        paged = db.pics.getPagedPending(page=pgr.idx, size=pgr.size)
        lg.info(f"[sim:load] pend reload, idx[{pgr.idx}] size[{pgr.size}] got[{len(paged)}]")
        now.sim.assPend = paged

    # Only rebuild gvPnd if pending data changed
    if needReload:
        gvPnd = gvs.mkPndGrid(now.sim.assPend, onEmpty=[
            dbc.Alert("Please find the similar images..", color="secondary", className="text-center m-5"),
        ])
    else:
        gvPnd = noUpd

    # Update pending tab state based on cntPn
    tabDisabled = cntPn < 1
    tabLabel = f"pending ({cntPn})" if cntPn >= 1 else "pending"

    # Only update now if there were actual changes
    nowChanged = needReload or (pagerData is not None)
    nowDict = now.toDict() if nowChanged else noUpd

    activeTab = now.sim.activeTab if now.sim.activeTab else k.tabCur

    return [
        gvSim, gvPnd,
        nfy.toDict(), nowDict,
        pagerData.toDict() if pagerData else noUpd,
        tabDisabled, tabLabel, activeTab
    ]


#------------------------------------------------------------------------
# Update status counters - Using CLIENT-SIDE callbacks for performance
#------------------------------------------------------------------------

ccbk(
    cbkFn( "similar", "onCardSelectClicked" ),
    out(ks.sto.ste, "data"),
    [inp({"type": "card-select", "id": ALL}, "n_clicks")],
    prevent_initial_call=True
)


#------------------------------------------------------------------------
# Initialize client-side selection state when assets load
#------------------------------------------------------------------------
ccbk(
    cbkFn( "similar", "onNowSyncToDummyInit" ),
    out({"type": "dummy-output", "id": "init-selection"}, "children"),
    inp(ks.sto.now, "data"),
    inp(ks.sto.ste, "data"),
    prevent_initial_call="initial_duplicate"
)


#------------------------------------------------------------------------
# Update all button states based on current data
#------------------------------------------------------------------------
@cbk(
    [
        out(k.btnFind, "disabled"),
        out(k.btnClear, "disabled"),
        out(k.btnReset, "disabled"),
        out(k.btnOkAll, "disabled"),
        out(k.btnRmAll, "disabled"),
        out(k.btnRmSel, "disabled"),
        out(k.btnOkSel, "disabled"),
    ],
    [
        inp(ks.sto.now, "data"),
        inp(ks.sto.ste, "data"),
        inp(ks.sto.cnt, "data"),
    ],
    prevent_initial_call="initial_duplicate"
)
def sim_UpdateButtons(dta_now, dta_ste, dta_cnt):
    now = Now.fromDict(dta_now)
    ste = Ste.fromDict(dta_ste) if dta_ste else Ste()
    cnt = Cnt.fromDict(dta_cnt)

    # 檢查是否有任務運行
    from mod.mgr.tskSvc import mgr
    isTaskRunning = False
    if mgr:
        for tskId, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                isTaskRunning = True
                break

    # Find 按鈕邏輯
    cntNo = cnt.ass - cnt.simOk if cnt else 0
    cntPn = cnt.simPnd if cnt else 0
    disFind = cntNo <= 0 or (cntPn >= cntNo) or isTaskRunning

    # Clear 按鈕邏輯 (只清除搜尋記錄，保留已解決的)
    cntSrchd = db.pics.countHasSimIds(isOk=0) if not isTaskRunning else 0
    disClear = cntSrchd <= 0 or isTaskRunning

    # Reset 按鈕邏輯 (清除所有記錄)
    cntOk = cnt.simOk if cnt else 0
    disReset = cntOk <= 0 and cntPn <= 0 or isTaskRunning

    # 當前資產相關按鈕
    cntAssets = len(now.sim.assCur) if now.sim.assCur else 0
    disOk = cntAssets <= 0
    disDel = cntAssets <= 0

    # 選擇相關按鈕
    cntSel = len(ste.selectedIds) if ste.selectedIds else 0
    disRm = cntSel == 0
    disRS = cntSel == 0

    lg.info(f"[sim:UpdBtns] disFind[{disFind}]")

    return disFind, disClear, disReset, disOk, disDel, disRm, disRS


#------------------------------------------------------------------------
# Handle group view button click
#------------------------------------------------------------------------
@cbk(
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
    if not ctx.triggered: return noUpd.by(2)

    # Check if any button was actually clicked
    if not any(clks): return noUpd.by(2)

    now = Now.fromDict(dta_now)

    trgId = ctx.triggered_id

    if not trgId: return noUpd.by(2)

    assId = trgId["id"]

    lg.info(f"[sim:vgrp] switch: id[{assId}] clks[{clks}]")

    asset = db.pics.getById(assId)
    if not asset: return noUpd.by(2)

    now.sim.assAid = asset.autoId
    now.sim.assCur = db.pics.getSimAssets(asset.autoId, db.dto.simIncRelGrp)

    if DEBUG: lg.info(f"[sim:vgrp] Loaded {len(now.sim.assCur)} assets for group")

    return now.toDict(), k.tabCur  # Switch to current tab


#========================================================================
# trigger modal
#========================================================================
@cbk(
    [
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    [
        inp(k.btnFind, "n_clicks"),
        inp(k.btnClear, "n_clicks"),
        inp(k.btnReset, "n_clicks"),
        inp(k.btnRmSel, "n_clicks"),
        inp(k.btnOkSel, "n_clicks"),
        inp(k.btnOkAll, "n_clicks"),
        inp(k.btnRmAll, "n_clicks"),
    ],
    [
        ste(ks.sto.now, "data"),
        ste(ks.sto.cnt, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
        ste(ks.sto.ste, "data"),
        ste(k.cbxNChkOkAll, "value"),
        ste(k.cbxNChkRmSel, "value"),
        ste(k.cbxNChkOkSel, "value"),
        ste(k.cbxNChkRmAll, "value"),
    ],
    prevent_initial_call=True
)
def sim_RunModal(
    clk_fnd, clk_clr, clk_rst, clk_rm, clk_rs, clk_ok, clk_ra,
    dta_now, dta_cnt, dta_mdl, dta_tsk, dta_nfy, dta_ste,
    nchkOkAll, nchkRmSel, ncRS, ncRA
):
    if not clk_fnd and not clk_clr and not clk_rst and not clk_rm and not clk_rs and not clk_ok and not clk_ra:
        lg.info( f"[sim:RunModal] fnd[{clk_fnd}] clr[{clk_clr}] rst[{clk_rst}] rm[{clk_rm}] rs[{clk_rs}] ok[{clk_ok}] ra[{clk_ra}]" )
        return noUpd.by(4)

    trgId = getTrgId()

    now = Now.fromDict(dta_now)
    cnt = Cnt.fromDict(dta_cnt)
    mdl = Mdl.fromDict(dta_mdl)
    tsk = Tsk.fromDict(dta_tsk)
    nfy = Nfy.fromDict(dta_nfy)
    ste = Ste.fromDict(dta_ste)

    retNow, retTsk = noUpd, noUpd



    # Check if any task is already running
    from mod.mgr.tskSvc import mgr
    if mgr:
        for tid, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                nfy.warn(f"Task already running, please wait for it to complete")
                return noUpd.by(4).updFr(0, nfy)

    if tsk.id:
        if mgr and mgr.getInfo(tsk.id):
            ti = mgr.getInfo(tsk.id)
            if ti and ti.status in ['pending', 'running']:
                nfy.warn(f"[similar] Task already running: {tsk.id}")
                return noUpd.by(4).updFr(0, nfy)
            # lg.info(f"[similar] Clearing completed task: {tsk.id}")
            tsk.id = None
            tsk.cmd = None

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    #------------------------------------------------------------------------
    if trgId == k.btnClear:
        cntRs = db.pics.countHasSimIds(isOk=0)
        if cntRs <= 0:
            nfy.warn(f"[similar] No search records to clear")
            return noUpd.by(4).updFr(0, nfy)

        mdl.reset()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.clear
        mdl.msg = [
            f"Clear search records but keep resolved items?", htm.Br(),
            f"Will clear ({cntRs}) search records", htm.Br(),
            htm.B("Resolved items (simOk=1) will be kept"), htm.Br(),
        ]

    #------------------------------------------------------------------------
    elif trgId == k.btnReset:
        cntOk = db.pics.countSimOk(isOk=1)
        cntRs = db.pics.countHasSimIds()
        if cntOk <= 0 and cntRs <= 0:
            nfy.warn(f"[similar] DB does not contain any similarity records")
            return noUpd.by(4).updFr(0, nfy)

        mdl.reset()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.reset
        mdl.msg = [
            f"Are you sure you want to reset all records?", htm.Br(),
            f"include resolved({cntOk}) and search({cntRs})", htm.Br(),
            htm.B("This operation cannot be undone"), htm.Br(),
            "You may need to perform all similarity searches again."
        ]

    #------------------------------------------------------------------------
    elif trgId == k.btnRmSel:
        ass = ste.getSelected(now.sim.assCur)
        cnt = len(ass)

        lg.info(f"[sim:delSels] {cnt} assets selected")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.selRm
            mdl.msg = [
                f"Are you sure you want to Delete select images( {cnt} )?", htm.Br(),
                htm.B("This operation cannot be undone"),
            ]

            if nchkRmSel:
                retTsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnOkSel:
        assSel = ste.getSelected(now.sim.assCur)
        assAll = now.sim.assCur
        cnt = len(assSel)

        lg.info(f"[sim:resolveSels] {cnt} assets selected")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.selOk
            mdl.msg = [
                f"Are you sure you want to Resolve selected images( {cnt} ) and Delete others( {len(assAll) - cnt} )?", htm.Br(),
                htm.B("This operation cannot be undone"),
            ]

            if ncRS:
                retTsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnRmAll:
        ass = now.sim.assCur
        cnt = len(ass)

        lg.info(f"[sim:delAll] {cnt} assets to delete")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.allRm
            mdl.msg = [
                f"Are you sure you want to Delete ALL current images( {cnt} )?", htm.Br(),
                htm.B("This operation cannot be undone"),
            ]

            if ncRA:
                retTsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnOkAll:
        ass = now.sim.assCur
        cnt = len(ass)

        lg.info(f"[sim:reslove] {cnt} assets")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.allOk
            mdl.msg = f"Are you sure mark resloved current images( {cnt} )?"

            if nchkOkAll:
                retTsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnFind:
        if cnt.vec <= 0:
            nfy.error("No vector data to process")
            now.sim.clearAll()
            return noUpd.by(4).updFr( 0, [nfy, now] )

        thMin = db.dto.simMin
        thMax = db.dto.simMax

        lg.info(f"[thMin/thMax] min[{thMin}] max[{thMax}]")

        asset: Optional[models.Asset] = None

        # asset from url
        isFromUrl = False
        if now.sim.assFromUrl:
            ass = now.sim.assFromUrl  #consider read from db again?
            if ass:
                if ass.simOk != 1:
                    lg.info(f"[sim] use selected asset id[{ass.id}]")
                    asset = ass
                    isFromUrl = True
                else:
                    nfy.info(f"[sim] the asset #{ass.autoId} already resolved")
                    now.sim.assFromUrl = None
                    return noUpd.by(4).updFr( 0, [nfy, now] )
            else:
                nfy.warn(f"[sim] not found dst assetId[{now.sim.assFromUrl}]")
                now.sim.assFromUrl = None
                return noUpd.by(4).updFr( 0, [nfy, now] )

        # find from db
        if not asset:
            ass = db.pics.getAnyNonSim()
            if ass:
                asset = ass
                lg.info(f"[sim] found non-simOk #{ass.autoId} assetId[{ass.id}]")

        if not isFromUrl:
            now.sim.clearAll()
            retNow = now

        if not asset:
            nfy.warn(f"[sim] not any asset to find..")
        else:
            now.sim.assAid = asset.autoId

            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.fnd
            tsk = mdl.mkTsk()
            mdl.reset()

            lg.info(f"[sim:run] now.sim.assAid[{now.sim.assAid}]")

            # only find auto trigger tsk
            retTsk = tsk
            retNow = now
            # mdl.msg = [
            #     f"Begin finding similar?", htm.Br(),
            #     f"threshold[{thMin:.2f}-{thMax:.2f}]]",
            # ]


    lg.info(f"[similar] modal[{mdl.id}] cmd[{mdl.cmd}]")

    return noUpd.by( 4 ).updFr( 0, [nfy, retNow, mdl, retTsk] )


#========================================================================
# task acts
#========================================================================
from mod.models import IFnProg


def queueNext(sto: tskSvc.ITaskStore):
    nfy, tsk = sto.nfy, sto.tsk

    ass = db.pics.getAnyNonSim()
    if ass:
        lg.info(f"[sim] auto found non-simOk assetId[{ass.id}]")

        mdl = models.Mdl()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.fnd
        mdl.args = {'thMin': db.dto.simMin, 'thMax': db.dto.simMax}

        ntsk = mdl.mkTsk()
        ntsk.args['assetId'] = ass.id

        sto.tsk.nexts.append(ntsk)

        sto.tsk = tsk
        nfy.success([f"Auto-Find next: #{ass.autoId}"])


def sim_FindSimilar(doReport: IFnProg, sto: tskSvc.ITaskStore):
    from db import sim

    nfy, now, tsk = sto.nfy, sto.now, sto.tsk

    maxDepth = db.dto.simMaxDepths
    maxItems = db.dto.simMaxItems
    thMin, thMax = db.dto.simMin, db.dto.simMax

    thMin = co.vad.float(thMin, 0.9)
    thMax = co.vad.float(thMax, 1.0)

    isFromUrl = now.sim.assFromUrl is not None and now.sim.assFromUrl.autoId is not None

    lg.info(f"[sim:fnd] config maxDepths[{maxDepth}] maxItems[{maxItems}]")

    # Clear URL guidance to avoid duplicate searches
    if now.sim.assFromUrl:
        now.sim.assFromUrl = None

    try:
        lg.info(f"[sim:fnd] now.sim.assAid[{now.sim.assAid}]")
        doReport(1, f"prepare..")

        # Create progress reporter
        autoReport = sim.createProgressReporter(doReport)

        # Find asset candidate
        try:
            asset = sim.findAssetCandidate(now.sim.assAid, tsk.args)
        except RuntimeError as e:
            if "already searched" in str(e):
                now.sim.assCur = []
                return sto, [str(e)]
            raise e

        # Search for similar assets
        sch = sim.searchSimilar(asset, thMin, thMax, autoReport, isFromUrl, doReport)

        if not sch.hasVector:
            nfy.info(f"Asset #{sch.asset.autoId} has no vector stored")
            return sto, f"Asset #{sch.asset.autoId} has no vector stored"

        if not sch.foundSimilar:
            nfy.info(f"Asset #{sch.asset.autoId} no similar found")
            return sto, f"Asset #{sch.asset.autoId} no similar found"

        # Process children assets in similarity tree
        asset = sch.asset
        doneIds = sim.processChildren(asset, sch.bseInfos, sch.simAids, thMin, thMax, maxDepth, maxItems, doReport)

        # Auto mark single items as resolved
        db.pics.setSimAutoMark()

        # Process groups and mark assets
        maxGroups = db.dto.simCondMaxGroups if db.dto.simCondGrpMode else 1
        condAssets = sim.processCondGroup(asset, 1)

        # Search for additional groups if in group mode
        grps = sim.searchCondGroups(condAssets, maxGroups, thMin, thMax, maxDepth, maxItems, doReport)

        doReport(95, f"Finalizing {grps.groupCount} group(s) with {len(grps.allGroupAssets)} total assets")
        time.sleep(0.5)

        # Update state
        now.sim.assAid = asset.autoId
        now.sim.assCur = grps.allGroupAssets
        now.sim.activeTab = k.tabCur

        lg.info(f"[sim:fnd] done, found {grps.groupCount} group(s) with {len(grps.allGroupAssets)} assets")

        if not now.sim.assCur: raise RuntimeError(f"No groups found")

        doReport(100, f"Completed finding {grps.groupCount} similar photo group(s)")

        # Generate completion message
        if db.dto.simCondGrpMode:
            msg = [f"Found {grps.groupCount} similar photo group(s) with {len(grps.allGroupAssets)} total photos"]
            if grps.groupCount >= maxGroups: msg.append(f"Reached maximum group limit ({maxGroups} groups).")
        else:
            cntInfos = len(sch.bseInfos)
            msg = [f"Found {len(sch.bseInfos)} similar photos for #{asset.autoId}"]
            cntAll = len(doneIds)
            if cntAll > cntInfos:
                msg.append(f"include ({cntAll - cntInfos}) asset extra tree in similar tree.")
            if cntAll >= maxItems:
                msg.append(f"Reached maximum search limit ({maxItems} items).")

        # Auto-select assets if enabled
        lg.info(f"[sim:fnd] Starting auto-selection check, enable={db.dto.auSelEnable}")
        autoSelectedIds = sim.getAutoSelectedAssets(now.sim.assCur) if now.sim.assCur else []
        if autoSelectedIds:
            lg.info(f"[sim:fnd] Auto-selected {len(autoSelectedIds)} assets: {autoSelectedIds}")
            sto.ste.selectedIds = autoSelectedIds
            sto.ste.cntTotal = len(now.sim.assCur)
            lg.info(f"[sim:fnd] Updated ste store: selectedIds={sto.ste.selectedIds}, cntTotal={sto.ste.cntTotal}")
        else:
            lg.info(f"[sim:fnd] No assets auto-selected")

        nfy.success(msg)
        return sto, msg

    except Exception as e:
        msg = f"[sim:fnd] Similar search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()
        raise RuntimeError(msg)



def sim_ClearSims(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt, tsk = sto.nfy, sto.now, sto.cnt, sto.tsk

    try:
        keepSimOk = tsk.cmd == ks.cmd.sim.clear

        doReport(10, "Preparing to clear similarity records...")

        if keepSimOk:
            cntRs = db.pics.countHasSimIds(isOk=0)
            if cntRs <= 0:
                msg = "No search records to clear"
                lg.info(msg)
                nfy.info(msg)
                return sto, msg
        else:
            cntOk = db.pics.countSimOk(isOk=1)
            cntRs = db.pics.countHasSimIds()
            if cntOk <= 0 and cntRs <= 0:
                msg = "No similarity records to clear"
                lg.info(msg)
                nfy.info(msg)
                return sto, msg

        doReport(30, "Clearing similarity records from database...")

        db.pics.clearAllSimIds(keepSimOk=keepSimOk)

        doReport(90, "Updating dynamic data...")

        now.sim.assFromUrl = None
        now.sim.clearAll()

        doReport(100, "Clear completed")

        if keepSimOk:
            msg = f"Successfully cleared search records but kept resolved items"
        else:
            msg = f"Successfully cleared all similarity records"

        lg.info(f"[sim_Clear] {msg}")
        nfy.success(msg)

        return sto, msg

    except Exception as e:
        msg = f"Failed to clear similarity records: {str(e)}"
        lg.error(f"[sim_Clear] {msg}")
        lg.error(traceback.format_exc())
        nfy.error(msg)
        raise RuntimeError(msg)



def sim_SelectedDelete(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt, ste = sto.nfy, sto.now, sto.cnt, sto.ste
    try:
        assAlls = now.sim.assCur
        assSels = ste.getSelected(assAlls) if ste else []
        assLefts = [a for a in assAlls if a.autoId not in {s.autoId for s in assSels}]

        cntSelect = len(assSels)
        msg = f"[sim] Delete Selected Assets( {cntSelect} ) Success!"

        if not assSels or cntSelect == 0: raise RuntimeError("Selected not found")

        immich.trashByAssets(assSels)
        db.pics.deleteBy(assSels)

        db.pics.setResloveBy(assLefts)  # set unselected to resloved

        now.sim.clearAll()

        if not db.dto.autoNext:
            now.sim.activeTab = k.tabPnd
        else:
            queueNext(sto)

        nfy.success(msg)

        return sto, msg
    except Exception as e:
        msg = f"[sim] Delete selected failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()

        raise RuntimeError(msg)


def sim_SelectedReslove(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt, ste = sto.nfy, sto.now, sto.cnt, sto.ste
    try:
        assAlls = now.sim.assCur
        assSels = ste.getSelected(assAlls) if ste else []
        assOthers = [a for a in assAlls if a.autoId not in {s.autoId for s in assSels}]

        cntSelect = len(assSels)
        cntOthers = len(assOthers)
        msg = f"[sim] Resolve Selected Assets( {cntSelect} ) and Delete Others( {cntOthers} ) Success!"

        if not assSels or cntSelect == 0: raise RuntimeError("Selected not found")

        lg.info(f"[sim:selOk] reslove assets[{cntSelect}] delete[ {cntOthers} ]")

        # Delete other assets first to maintain reference integrity
        if assOthers:
            immich.trashByAssets(assOthers)
            db.pics.deleteBy(assOthers)

        # Then resolve selected assets
        db.pics.setResloveBy(assSels)

        now.sim.clearAll()

        if not db.dto.autoNext:
            now.sim.activeTab = k.tabPnd
        else:
            queueNext(sto)

        return sto, msg
    except Exception as e:
        msg = f"[sim] Resolve selected failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()

        raise RuntimeError(msg)


def sim_AllReslove(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assets = now.sim.assCur
        cntAll = len(assets)
        msg = f"[sim] set Resloved Assets( {cntAll} ) Success!"

        if not assets or cnt == 0: raise RuntimeError("Current Assets not found")
        lg.info(f"[sim:allReslove] reslove assets[{cntAll}] ")

        db.pics.setResloveBy(assets)

        now.sim.clearAll()

        if not db.dto.autoNext:
            now.sim.activeTab = k.tabPnd
        else:
            queueNext(sto)

        return sto, msg
    except Exception as e:
        msg = f"[sim] Resloved All failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()

        raise RuntimeError(msg)


def sim_AllDelete(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assets = now.sim.assCur
        cntAll = len(assets)
        msg = f"[sim] Delete All Assets( {cntAll} ) Success!"

        if not assets or cntAll == 0: raise RuntimeError("Current Assets not found")

        lg.info(f"[sim:allDel] delete assets[{cntAll}] ")

        immich.trashByAssets(assets)
        db.pics.deleteBy(assets)

        now.sim.clearAll()

        if not db.dto.autoNext:
            now.sim.activeTab = k.tabPnd
        else:
            queueNext(sto)

        return sto, msg
    except Exception as e:
        msg = f"[sim] Delete all failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()

        raise RuntimeError(msg)



#========================================================================
# Set up global functions
#========================================================================
mapFns[ks.cmd.sim.fnd] = sim_FindSimilar
mapFns[ks.cmd.sim.clear] = sim_ClearSims
mapFns[ks.cmd.sim.reset] = sim_ClearSims
mapFns[ks.cmd.sim.selOk] = sim_SelectedReslove
mapFns[ks.cmd.sim.selRm] = sim_SelectedDelete
mapFns[ks.cmd.sim.allOk] = sim_AllReslove
mapFns[ks.cmd.sim.allRm] = sim_AllDelete
