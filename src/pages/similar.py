import traceback
from typing import Optional
import time
import numpy as np

import immich
import db
from conf import ks, co
from dsh import dash, htm, dcc, cbk, dbc, inp, out, ste, getTrgId, noUpd, ctx, ALL
from util import log
from mod import mapFns, models, tskSvc
from mod.models import Mdl, Now, Cnt, Nfy, Pager, Tsk
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

    btnFind = "sim-btn-find"
    btnClear = "sim-btn-clear"
    btnCbxRm = "sim-btn-CbxRm"
    btnCbxRS = "sim-btn-CbxRS"
    btnCbxOk = "sim-btn-CbxOk"
    btnCbxRA = "sim-btn-CbxRA"
    cbxNCOk = "sim-btn-CbxNCOk"
    cbxNCRm = "sim-btn-CbxNCRm"
    cbxNCRS = "sim-btn-CbxNCRS"
    cbxNCRA = "sim-btn-CbxNCRA"

    tabs = 'sim-tabs'
    tabCur = "tab-current"
    tabPnd = "tab-pending"
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

        htm.Div([
            htm.H3(f"{ks.pg.similar.name}"),
            htm.Small(f"{ks.pg.similar.desc}", className="text-muted")
        ], className="body-header"),


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
                    ])
                ], className="mb-4"),
            ], width=4),

            dbc.Col([

                cardSets.renderCard(),

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
                active_tab=k.tabCur,
                children=[
                    dbc.Tab(
                        label="current",
                        tab_id=k.tabCur,
                        children=[

                            # Action buttons
                            htm.Div([

                                htm.Div([
                                ], className="left"),


                                htm.Div([

                                    htm.Div([
                                        dbc.Button("------", id=k.btnCbxRm, color="danger", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNCRm, label="No-Confirm", className="sm"),
                                    ]
                                    ),

                                    htm.Div([
                                        dbc.Button("------", id=k.btnCbxRS, color="success", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNCRS, label="No-Confirm", className="sm")
                                    ]),

                                    htm.Div([
                                        dbc.Button("❌ Delete All", id=k.btnCbxRA, color="danger", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNCRA, label="No-Confirm", className="sm")
                                    ]),

                                    htm.Div([
                                        dbc.Button("✅ Keep All", id=k.btnCbxOk, color="success", size="sm", disabled=True),
                                        htm.Br(),
                                        dbc.Checkbox(id=k.cbxNCOk, label="No-Confirm", className="sm")
                                    ]),

                                ], className="right"),


                            ],
                                className="tab-acts"
                            ),


                            # dbc.Spinner(
                            htm.Div(id=k.gvSim),
                            #     color="success",type="border",spinner_style={"width": "3rem", "height": "3rem"},
                            # ),
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

                                # Grid view
                                # dbc.Spinner(
                                htm.Div(id=k.gvPnd),
                                # color="success", type="border", spinner_style={"width": "3rem", "height": "3rem"},
                                # ),

                                # bottom pager
                                *pager.createPager(pgId=k.pagerPnd, idx=1, btnSize=9, className="mt-3"),

                                # Main pager (store only)
                                *pager.createStore(pgId=k.pagerPnd),
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

    now.sim.activeTab = active_tab
    lg.info(f"[sim:tab] Tab changed to: {active_tab} (from: {now.sim.activeTab})")

    return now.toDict()


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


# The pager initialization is now handled by regCallbacks with secondaryIds


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
        if not now.sim.assFromUrl:
            return noUpd.by(2)

        now.sim.assFromUrl = None
        # now.sim.assId = None # clean here will make refresh assId failed
        return now.toDict(), noUpd

    ass = models.Asset.fromDict(dta_ass)

    lg.info(f"[sim:sync] asset from url: #{ass.autoId} id[{ass.id}]")

    now.sim.assFromUrl = ass
    now.sim.assId = ass.id

    thMin = co.vad.float(db.dto.simMin, 0.7)
    thMax = co.vad.float(db.dto.simMax, 1.0)

    mdl = Mdl()
    mdl.id = ks.pg.similar
    mdl.cmd = ks.cmd.sim.fdSim
    mdl.name = f'Find similar for #{ass.autoId}'
    mdl.msg = f'Search images similar to {ass.originalFileName} with threshold [{thMin:.2f} - {thMax:.2f}]'
    mdl.args = {'thMin': thMin, 'thMax': thMax, 'fromUrl': True}

    tsk = mdl.mkTsk()

    lg.info(f"[sim:sync] to task: {tsk}")

    return now.toDict(), tsk.toDict()


#------------------------------------------------------------------------
# onStatus
#------------------------------------------------------------------------
@cbk(
    [
        out(k.txtCntOk, "children"),
        out(k.txtCntRs, "children"),
        out(k.txtCntNo, "children"),
        out(k.btnFind, "disabled"),
        out(k.btnClear, "disabled"),
        out(k.btnCbxOk, "disabled"),
        out(k.btnCbxRA, "disabled"),
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
    ],
    prevent_initial_call="initial_duplicate"
)
def sim_Load(dta_now, dta_nfy):
    #lg.info( f"[sim:load] now: {dta_now}" )

    now = Now.fromDict(dta_now)
    nfy = Nfy.fromDict(dta_nfy)

    trgId = getTrgId()

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

    cntAssets = len(now.sim.assCur) if now.sim.assCur else -1
    disOk = cntAssets <= 0
    disDel = cntAssets <= 0

    if cntAssets >= 1:
        #lg.info(f"[sim:load] assets: {now.sim.assets[0]}")
        pass

    gvSim = []

    if cntNo <= 0:
        nfy.info("Not have any vectors, please do generate vectors first")

    gvSim = gvs.mkGrid(now.sim.assCur, onEmpty=[
        dbc.Alert("Please find the similar images..", color="secondary", className="text-center m-5"),
    ])

    # Initialize or get pager
    pgr = now.sim.pagerPnd
    if not pgr:
        lg.info("[sim:load] create pager")
        pgr = Pager(idx=1, size=20)
        now.sim.pagerPnd = pgr

    # Update pager total count
    pagerData = None
    oldPn = pgr.cnt
    if pgr.cnt != cntPn:
        pgr.cnt = cntPn
        # Keep current page if still valid, otherwise reset to last valid page
        totalPages = (cntPn + pgr.size - 1) // pgr.size if cntPn > 0 else 1
        if pgr.idx > totalPages:
            pgr.idx = max(1, totalPages)
        now.sim.pagerPnd = pgr
        # Only update pager store if count actually changed
        if oldPn != cntPn: pagerData = pgr

    lg.info(f"--------------------------------------------------------------------------------")
    lg.info(f"[sim:load] trig[{trgId}] cntNo[{cntNo}] cntOk[{cntOk}] cntPn[{cntPn}]({oldPn}) now[{cntAssets}] assId[{now.sim.assId}]")
    # lg.info(f"[sim:load] tgId[{trgId}] assId[{now.sim.assId}] assCur[{len(now.sim.assCur)}] assPend[{len(now.sim.assPend)}]")

    # Load pending data - reload if count changed or no data
    needReload = False
    if cntPn > 0:
        if not now.sim.assPend or len(now.sim.assPend) == 0:
            needReload = True
        elif oldPn != cntPn:
            needReload = True
            lg.info(f"[sim:load] Pending count changed from {oldPn} to {cntPn}, reloading data")

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
        cntOk, cntPn, cntNo,
        disFind, disCler, disOk, disDel,
        gvSim, gvPnd,
        nfy.toDict(), nowDict,
        pagerData.toDict() if pagerData else noUpd,
        tabDisabled, tabLabel, activeTab
    ]


#------------------------------------------------------------------------
# Update status counters
#------------------------------------------------------------------------
@cbk(
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

    # lg.info(f"[sim:select] any[{hasClk}] {clks_crd}")

    now = Now.fromDict(dta_now)
    nfy = Nfy.fromDict(dta_nfy)

    if ctx.triggered and now.sim.assCur:
        trgId = ctx.triggered_id
        tid = trgId['id']

        # 找到被點擊的資產並切換選擇狀態
        targetAss = None
        for ass in now.sim.assCur:
            if ass.id == tid:
                ass.view.selected = not ass.view.selected
                targetAss = ass
                lg.info(f'[header-click] toggled: {ass.autoId}, selected: {ass.view.selected}')
                break

        if targetAss:
            # 增量更新 assSelect
            if not now.sim.assSelect:
                now.sim.assSelect = []

            if targetAss.view.selected:
                # 新增到選擇清單
                if not any(a.id == targetAss.id for a in now.sim.assSelect):
                    now.sim.assSelect.append(targetAss)
            else:
                # 從選擇清單移除
                now.sim.assSelect = [a for a in now.sim.assSelect if a.id != targetAss.id]

            lg.info(f'[sim:select] Selected: {len(now.sim.assSelect)}/{len(now.sim.assCur)}')

    return now.toDict()


#------------------------------------------------------------------------
# Update button state based on selections
#------------------------------------------------------------------------
@cbk(
    [
        out(k.btnCbxRm, "children"),
        out(k.btnCbxRm, "disabled"),
        out(k.btnCbxRS, "children"),
        out(k.btnCbxRS, "disabled"),
    ],
    inp(ks.sto.now, "data"),
    prevent_initial_call=True
)
def sim_OnNowChangeSelects(dta_now):
    now = Now.fromDict(dta_now)

    cntAll = len(now.sim.assCur)
    cntSel = len(now.sim.assSelect)
    cntDiff = cntAll - cntSel

    # if selCnt: lg.info(f"[sim:slect] selCnt[{selCnt}]")

    btnTextRm = f"❌ Delete( {cntSel} ) and ✅ Keep others"
    btnTextRS = f"✅ Keep( {cntSel} ) and ❌ delete others"
    btnDisabled = cntSel == 0

    return btnTextRm, btnDisabled, btnTextRS, btnDisabled


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
    assId = trgId["id"]

    lg.info(f"[sim:vgrp] switch: id[{assId}] clks[{clks}]")

    now.sim.assId = assId
    now.sim.assCur = db.pics.getSimAssets(assId, db.dto.simIncRelGrp)
    now.sim.assSelect = []

    if DEBUG: lg.info(f"[sim:vgrp] Loaded {len(now.sim.assCur)} assets for group")

    return now.toDict(), k.tabCur  # Switch to current tab


#========================================================================
# trigger modal
#========================================================================
@cbk(
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
        inp(k.btnCbxRS, "n_clicks"),
        inp(k.btnCbxOk, "n_clicks"),
        inp(k.btnCbxRA, "n_clicks"),
    ],
    [
        ste(ks.sto.now, "data"),
        ste(ks.sto.cnt, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
        ste(k.cbxNCOk, "value"),
        ste(k.cbxNCRm, "value"),
        ste(k.cbxNCRS, "value"),
        ste(k.cbxNCRA, "value"),
    ],
    prevent_initial_call=True
)
def sim_RunModal(clk_fnd, clk_clr, clk_rm, clk_rs, clk_ok, clk_ra, dta_now, dta_cnt, dta_mdl, dta_tsk, dta_nfy, ncOk, ncRm, ncRS, ncRA):
    if not clk_fnd and not clk_clr and not clk_rm and not clk_rs and not clk_ok and not clk_ra: return noUpd.by(4)

    trgId = getTrgId()

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
                return noUpd.by(4)
            # lg.info(f"[similar] Clearing completed task: {tsk.id}")
            tsk.id = None
            tsk.cmd = None

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    #------------------------------------------------------------------------
    if trgId == k.btnCbxOk:
        ass = now.sim.assCur
        cnt = len(ass)

        lg.info(f"[sim:reslove] {cnt} assets")

        if cnt > 0:
            mdl.reset()
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.allOk
            mdl.msg = f"Are you sure mark resloved current images( {cnt} )?"

            if ncOk:
                tsk = mdl.mkTsk()
                mdl.reset()
    #------------------------------------------------------------------------
    elif trgId == k.btnCbxRm:
        ass = now.sim.assSelect
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

            if ncRm:
                tsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnCbxRS:
        assSel = now.sim.assSelect
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
                tsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnCbxRA:
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
                tsk = mdl.mkTsk()
                mdl.reset()

    #------------------------------------------------------------------------
    elif trgId == k.btnClear:
        cntOk = db.pics.countSimOk(isOk=1)
        cntRs = db.pics.countHasSimIds()
        if cntOk <= 0 and cntRs <= 0:
            nfy.warn(f"[similar] DB does not contain any similarity records")
            return noUpd, nfy.toDict(), noUpd.by(2)

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
            now.sim.clearAll()
            return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

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
                    return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd
            else:
                nfy.warn(f"[sim] not found dst assetId[{now.sim.assFromUrl}]")
                now.sim.assFromUrl = None
                return mdl.toDict(), nfy.toDict(), now.toDict(), noUpd

        # find from db
        if not asset:
            ass = db.pics.getAnyNonSim()
            if ass:
                asset = ass
                lg.info(f"[sim] found non-simOk #{ass.autoId} assetId[{ass.id}]")

        if not isFromUrl:
            now.sim.clearAll()
        if not asset:
            nfy.warn(f"[sim] not any asset to find..")
        else:
            now.sim.assId = asset.id

            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.fdSim
            mdl.args = {'thMin': thMin, 'thMax': thMax, 'fromUrl': isFromUrl}
            tsk = mdl.mkTsk()
            mdl.reset()
            # mdl.msg = [
            #     f"Begin finding similar?", htm.Br(),
            #     f"threshold[{thMin:.2f}-{thMax:.2f}]]",
            # ]

    lg.info(f"[similar] modal[{mdl.id}] cmd[{mdl.cmd}]")

    return mdl.toDict(), nfy.toDict(), now.toDict(), tsk.toDict()


#========================================================================
# task acts
#========================================================================
from mod.models import IFnProg


def sim_ClearSims(doReport: IFnProg, sto: tskSvc.ITaskStore):
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

        now.sim.assFromUrl = None

        now.sim.clearAll()

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


def queueNext(sto: tskSvc.ITaskStore):
    now, nfy, tsk = sto.now, sto.nfy, sto.tsk

    ass = db.pics.getAnyNonSim()
    if ass:
        lg.info(f"[sim] auto found non-simOk assetId[{ass.id}]")

        mdl = models.Mdl()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.fdSim
        mdl.args = {'thMin': db.dto.simMin, 'thMax': db.dto.simMax}

        ntsk = mdl.mkTsk()
        ntsk.args['assetId'] = ass.id

        sto.tsk.nexts.append(ntsk)

        sto.tsk = tsk
        nfy.success([f"Auto-Find next: #{ass.autoId}"])


def sim_FindSimilar(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt, tsk = sto.nfy, sto.now, sto.cnt, sto.tsk

    thMin, thMax, isFromUrl = tsk.args.get("thMin"), tsk.args.get("thMax"), tsk.args.get("fromUrl", False)

    thMin = co.vad.float(thMin, 0.9)
    thMax = co.vad.float(thMax, 1.0)

    # 如果是從 URL 進入，清除引導避免重複搜尋
    if isFromUrl and now.sim.assFromUrl:
        lg.info(f"[sim:find] Clearing URL guidance for asset {now.sim.assFromUrl.autoId if now.sim.assFromUrl else 'unknown'}")
        now.sim.assFromUrl = None

    try:
        assetId = now.sim.assId
        simIds = []
        doneIds = []

        if not assetId and tsk.args.get('assetId'):
            lg.info(f"[sim:find] search from task args assetId[{assetId}]")
            assetId = tsk.args.get('assetId')

        if not assetId: raise RuntimeError(f"[tsk] sim.assId is empty")

        doReport(1, f"prepare..")

        asset = db.pics.getById(assetId)

        if not asset: raise RuntimeError(f"[sim:find] not found assetId[{assetId}]")

        lg.info(f"[sim:find] search assetId[{assetId}] thresholds[{thMin:.2f}-{thMax:.2f}]")

        cntFnd = 0

        #------------------------------------------------
        # auto calc progress report
        #------------------------------------------------
        def autoReport(msg):
            cntAll = db.pics.count()
            cntOk = db.pics.countSimOk(1)
            doReport(round(cntOk / cntAll * 100, 2), msg)
            return cntOk, cntAll


        #------------------------------------------------
        # while process
        #------------------------------------------------
        while True:
            if cntFnd <= 0:
                msg = f"[sim:find] Searching #{asset.autoId}, thresholds[{thMin:.2f}-{thMax:.2f}]"
                doReport(10, msg)

            time.sleep(0.1)

            # will contain at least itself
            cntFnd += 1
            bseVec, bseInfos = db.vecs.findSimiliar(asset.id, thMin, thMax)

            #------------------------------------
            if not bseInfos:
                lg.warn(f"[sim:find] asset #{asset.autoId} not found any similar, may not store vector")
                db.pics.setVectoredBy(asset, 0)

                #------------------------------------
                # from url, stop
                #------------------------------------
                if isFromUrl:
                    msg = f"[sim:find] Asset #{asset.autoId} has no vector stored"
                    doReport(100, msg)
                    nfy.info(msg)
                    return sto, msg

                #------------------------------------
                # try find next
                #------------------------------------
                nextAss = db.pics.getAnyNonSim()
                if not nextAss:
                    msg = f"[sim:find] 沒有圖片可以繼續搜尋"
                    doReport(100, msg)
                    nfy.info(msg)
                    return sto, msg

                lg.info(f"[sim:find] No vector for #{asset.autoId}, next: #{nextAss.autoId}")

                autoReport(f"No vector for #{asset.autoId}, continuing to #{nextAss.autoId}...")

                asset = nextAss
                now.sim.assId = asset.id

                continue

            #------------------------------------
            # found simInfos
            #------------------------------------
            simIds = [i.id for i in bseInfos if not i.isSelf]

            #------------------------------------
            # only contains self
            #------------------------------------
            if not simIds:
                lg.info(f"[sim:find] NoFound #{asset.autoId}")
                db.pics.setSimInfos(asset.id, bseInfos, isOk=1)

                #------------------------------------
                # from url, stop
                #------------------------------------
                if isFromUrl:
                    msg = f"[sim:find] Asset #{asset.autoId} 沒有找到相似圖片"
                    doReport(100, msg)
                    nfy.info(msg)
                    return sto, msg
                #------------------------------------
                # try find next
                #------------------------------------
                nextAss = db.pics.getAnyNonSim()
                if not nextAss:
                    msg = f"[sim:find] 沒有圖片可以繼續搜尋"
                    doReport(100, msg)
                    nfy.info(msg)
                    return sto, msg

                lg.info(f"[sim:find] Next: #{nextAss.autoId}")

                autoReport(f"No similar found for #{asset.autoId}, continuing to #{nextAss.autoId}...")
                asset = nextAss
                now.sim.assId = nextAss.id

                continue

            #------------------------------------
            # 找到有相似圖片的，跳出迴圈繼續處理
            #------------------------------------
            break

        #------------------------------------------------
        # continue find children
        #------------------------------------------------

        #set main asset
        rootAuid = asset.autoId
        db.pics.setSimInfos(asset.id, bseInfos, GID=rootAuid)

        doneIds = {asset.id}

        # Get max depth setting (default 1 if not set)
        maxDepth = getattr(db.dto, 'simMaxDepths', 1)
        lg.info(f"[sim:find] Max depth for similar search: {maxDepth}")

        # Initialize queue with depth tracking (assId, depth)
        simQueue = [(sid, 0) for sid in simIds]

        # looping find all childs
        while simQueue:
            assId, curDepth = simQueue.pop(0)
            if assId in doneIds: continue

            doneIds.add(assId)
            autoReport(f"Processing children similar photo #{assId} depth({curDepth}) count({len(doneIds)})")

            try:
                lg.info(f"[sim:find] search child id[{assId}] at depth[{curDepth}]")
                cVec, cInfos = db.vecs.findSimiliar(assId, thMin, thMax)

                db.pics.setSimInfos(assId, cInfos, GID=rootAuid)

                ass = db.pics.getById(assId)

                # Only add children if we haven't reached max depth
                if curDepth < maxDepth:
                    for inf in cInfos:
                        if not inf.isSelf and inf.id not in doneIds:
                            simQueue.append((inf.id, curDepth + 1))
                            # Set GID immediately for found children
                            db.pics.setSimGIDs(inf.id, rootAuid)
                            lg.info(f"[sim:find] Added child {inf.id} at depth {curDepth + 1}")


            except Exception as ce:
                raise RuntimeError(f"Error processing similar image {assId}: {ce}")

        # auto mark
        db.pics.setSimAutoMark()

        doReport(95, f"Finalizing similar photo relationships")

        now.sim.assId = asset.id
        now.sim.assCur = db.pics.getSimAssets(asset.id, db.dto.simIncRelGrp)
        now.sim.assSelect = []
        now.sim.activeTab = k.tabCur

        lg.info(f"[sim:find] done, asset #{asset.autoId}")

        if not now.sim.assCur: raise RuntimeError(f"the get SimGroup not found by asset.id[{asset.id}]")

        doReport(100, f"Completed finding similar photos for #{asset.autoId}")

        cntInfos = len(bseInfos)
        msg = [f"Found {len(bseInfos)} similar photos for #{asset.autoId}"]

        cntAll = len(doneIds)
        if cntAll > cntInfos: msg.append(f"include ({cntAll - cntInfos}) asset extra tree in similar tree.")
        if cntFnd > 1: msg.append(f"Auto-processed {cntFnd} assets before finding similar photos.")

        nfy.success(msg)

        return sto, msg

    except Exception as e:
        msg = f"[sim:find] Similar search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        now.sim.clearAll()
        raise RuntimeError(msg)


def sim_SelectedDelete(doReport: IFnProg, sto: tskSvc.ITaskStore):
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assAlls = now.sim.assCur
        assSels = now.sim.assSelect
        assLefts = [a for a in assAlls if a.autoId not in {s.autoId for s in assSels}]

        cntSelect = len(assSels)
        msg = f"[sim] Delete Selected Assets( {cntSelect} ) Success!"

        if not assSels or cntSelect == 0: raise RuntimeError("Selected not found")

        for a in assSels:
            lg.info(f"[sim:delSelects] delete asset #[{a.autoId}] Id[ {a.id} ]")

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
    nfy, now, cnt = sto.nfy, sto.now, sto.cnt
    try:
        assAlls = now.sim.assCur
        assSels = now.sim.assSelect
        assOthers = [a for a in assAlls if a.autoId not in {s.autoId for s in assSels}]

        cntSelect = len(assSels)
        cntOthers = len(assOthers)
        msg = f"[sim] Resolve Selected Assets( {cntSelect} ) and Delete Others( {cntOthers} ) Success!"

        if not assSels or cntSelect == 0: raise RuntimeError("Selected not found")

        lg.info(f"[sim:selOk] reslove assets[{cntSelect}] delete[ {cntOthers} ]")

        # Delete other assets first to maintain reference integrity
        if assOthers:
            for a in assOthers:
                lg.info(f"[sim:selOk] delete asset #[{a.autoId}] Id[ {a.id} ]")

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
mapFns[ks.cmd.sim.fdSim] = sim_FindSimilar
mapFns[ks.cmd.sim.clear] = sim_ClearSims
mapFns[ks.cmd.sim.selOk] = sim_SelectedReslove
mapFns[ks.cmd.sim.selRm] = sim_SelectedDelete
mapFns[ks.cmd.sim.allOk] = sim_AllReslove
mapFns[ks.cmd.sim.allRm] = sim_AllDelete
