import traceback
from typing import Optional

import db
from conf import ks, co
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd, ctx, ALL
from util import log, models, task

lg = log.get(__name__)

dash.register_page(
    __name__,
    title=ks.pg.similar.name,
    name=ks.pg.similar.name,
    path=f'/{ks.pg.similar}',
    path_template=f'/{ks.pg.similar}/<assetId>',
)

class k:
    stoInitId = "store-init-id"

    txtCntOk = 'txt-cnt-ok'
    txtCntNo = 'txt-cnt-no'
    txtCntSel = 'txt-cnt-sel'
    slideTh = "inp-threshold-min"

    btnFind = "btn-find-sim"
    btnClear = "btn-clear-sim"
    btnDel = "btn-delete-selected"

    pager = "div-pager"
    grid = "div-grid-sim"


#========================================================================
def layout(assetId=None, **kwargs):
    # return flask.redirect('/target-page') #auth?

    if assetId:
        lg.info(f"[sim] from url assetId[{assetId}]")

        ass = db.pics.get(assetId)
        if ass and db.dyn.dto.simId != assetId:
            db.dyn.dto.simId = assetId
            lg.info(f"[sim] set current assetId[{assetId}]")

    return htm.Div([

        dbc.Row([
            dbc.Col(htm.H3(f"{ks.pg.similar.name}"), width=3),
            dbc.Col(htm.Small(f"{ks.pg.similar.desc}", className="text-muted"))
        ], className="mb-4"),


        htm.Div([

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("System Search Status"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(htm.Small("Searched", className="d-inline-block me-2"), width=5),
                                dbc.Col(dbc.Alert(f"0", id=k.txtCntOk, color="info", className="py-1 px-2 mb-2 text-center")),
                            ]),
                            dbc.Row([
                                dbc.Col(htm.Small("Unsearched", className="d-inline-block me-2"), width=5),
                                dbc.Col(dbc.Alert(f"0", id=k.txtCntNo, color="info", className="py-1 px-2 mb-2 text-center")),
                            ]),
                            dbc.Row([htm.Small("Shows vectorized data in the local db and whether similarity comparison has been performed with other assets", className="text-muted")])
                        ])
                    ], className="mb-4"),
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Search Settings"),
                        dbc.CardBody([
                            # dbc.Row([
                            #     dbc.Col([
                            #         dbc.Label("Similarity Method", className="txt-sm"),
                            #         dcc.Dropdown(
                            #             id=k.mthSim,
                            #             options=[
                            #                 {"value": ks.use.mth.cosine, "label": ks.use.mth.cosine.desc},
                            #                 {"value": ks.use.mth.euclid, "label": ks.use.mth.euclid.desc}
                            #             ],
                            #             value="cosine",
                            #             clearable=False,
                            #             className="mb-3"
                            #         ),
                            #     ]),
                            # ]),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Similarity Threshold Range", className="txt-sm"),
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.RangeSlider(
                                                id=k.slideTh,
                                                min=0,
                                                max=1,
                                                step=0.01,
                                                marks=ks.defs.thMarks,
                                                value=[0.8, 0.99],
                                                className="mb-0"
                                            ),
                                        ], className="mt-2"),
                                    ])
                                ]),
                            ]),

                            dbc.Row([htm.Small("A threshold range sets both minimum and maximum similarity levels for matches. It helps you find things that are similar enough to what you want, without being too strict or too loose with your matching criteria. (Usually the default setting works just fine)", className="text-muted")])
                        ])
                    ], className="mb-0"),
                ], width=8),
            ], className="mb-1"),

            dbc.Row([
                dbc.Col([
                    dbc.Button("Find Similar", id=k.btnFind, color="primary", size="lg", className="w-100", disabled=True),
                    htm.Small("note: if there are many pictures, it'll take a long time", className="text-muted ms-2"),
                ], width=6),

                dbc.Col([
                    dbc.Button("Clear Similar Status", id=k.btnClear, color="danger", size="lg", className="w-100", disabled=True),
                ], width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    htm.Div(id=k.txtCntSel, className="h4 mb-3"),
                ], width=8),

                dbc.Col([
                    dbc.Button(
                        "Delete Selected",
                        id=k.btnDel,
                        color="danger",
                        size="md",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=4),
            ], className="mt-4 mb-3", id="selected-photos-container", style={"display": ""}),


            htm.Div([

                # nav header
                htm.Div([

                    #left side
                    htm.Div( [

                        htm.Span("Menu1"),
                        htm.Span("Menu2"),

                    ] ),

                    #right side
                    htm.Div( [

                        htm.Button( "btn1" )
                    ]),

                ]),

                # content
                htm.Div([

                    htm.Div([ "1" ]),
                    htm.Div([ "2" ]),
                    htm.Div([ "3" ]),

                ]),

            ], className="taber"),

            # Results container with tabs
            dbc.Tabs([
                dbc.Tab([

                    dbc.Spinner(
                        htm.Div(id=k.grid),
                        color="primary",
                        type="border",
                        spinner_style={"width": "3rem", "height": "3rem"},
                        show_initially=True
                    ),

                ], label="Assets", tab_id="0"),

                dbc.Tab([

                         dbc.Row([
                            dbc.Col([
                                dbc.Pagination(id=k.pager, active_page=1, min_value=1, max_value=99, first_last=True, previous_next=True, fully_expanded=False, style={"display": ""})
                            ], className="d-flex justify-content-center mb-3")
                        ],
                            className="mt-2",
                        ),

                ], label="Unfinish Records", tab_id="1"),

            ], active_tab="0"),

            dcc.Store(id=k.stoInitId, data=assetId)
        ]),
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

#------------------------------------------------------------------------
# Update status counters
#------------------------------------------------------------------------
from ui import gridSimilar as gvs
@callback(
    [
        out(k.txtCntNo, "children"),
        out(k.txtCntOk, "children"),
        out(k.btnFind, "disabled"),
        out(k.btnClear, "disabled"),
        out(k.grid, "children"),
        out(ks.sto.nfy, "data", allow_duplicate=True),
    ],
    inp(ks.sto.now, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call='initial_duplicate'
)
def similar_onStatus(dta_now, dta_nfy):
    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)

    cntNo = db.pics.countSimOk(isOk=0)
    cntOk = db.pics.countSimOk(isOk=1)
    canFind = not cntNo >= 1
    canCler = not cntOk >= 1
    grid = []

    if cntNo <= 0:
        nfy.info("Not have any vectors, please do generate vectors first")

    if now.assets and len(now.assets) > 1:
        lg.info( f"now.assets[{len(now.assets)}]" )

        grid = gvs.createGrid(now.assets, gvs.mkImgCardSim)

    return cntNo, cntOk, canFind, canCler, grid, nfy.toStore()


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

    now = models.Now.fromStore(dta_now)
    nfy = models.Nfy.fromStore(dta_nfy)

    if ctx.triggered and now.assets and len(now.assets) > 1:
        trgId = ctx.triggered_id
        ass = next((a for a in now.assets if a.id == trgId.id), None)
        if ass:
            ass.selected = ctx.triggered[0]['value']
            # lg.info(f'[select] found: {ass.autoId}, selected: {ass.selected}, trgId: {trgId}')


    return now.toStore()


#========================================================================
# trigger modal
#========================================================================
@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
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
    if not clk_fnd and not clk_clr: return noUpd, noUpd, noUpd

    trgId = getTriggerId()

    now = models.Now.fromStore(dta_now)
    mdl = models.Mdl.fromStore(dta_mdl)
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)

    if tsk.id: return noUpd, noUpd, noUpd

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    if trgId == k.btnClear:
        cntOk = db.pics.countSimOk(isOk=1)
        if cntOk <= 0:
            nfy.warn(f"[similar] DB does not contain any similarity records")
            return noUpd, nfy.toStore(), noUpd

        mdl.reset()
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.clear
        mdl.msg = [
            f"Are you sure you want to delete all similarity records ({cntOk})?", htm.Br(),
            "This operation cannot be undone.", htm.Br(),
            "You may need to perform all similarity searches again."
        ]


    elif trgId == k.btnFind:
        if now.cntVec <= 0:
            nfy.error("No vector data to process")
            return mdl.toStore(), nfy.toStore(), noUpd

        thMin, thMax = thRange
        thMin = co.valid.float(thMin, 0.80)
        thMax = co.valid.float(thMax, 0.99)

        asset: Optional[models.Asset] = None

        if db.dyn.dto.simId:
            ass = db.pics.get(db.dyn.dto.simId)
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

        if not asset:
            nfy.warn(f"[sim] not any asset to find..")
        else:
            now.assets = [asset]

            mdl.reset()
            mdl.args = {'thMin': thMin, 'thMax': thMax}
            mdl.id = ks.pg.similar
            mdl.cmd = ks.cmd.sim.find
            mdl.msg = [
                f"Begin finding similar?", htm.Br(),
                f"threshold[{thMin:.2f}-{thMax:.2f}]]",
            ]

    lg.info(f"[similar] modal[{mdl.id}] cmd[{mdl.cmd}]")

    return mdl.toStore(), nfy.toStore(), now.toStore()


#========================================================================
# task acts
#========================================================================
def similar_FindSimilar(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: task.IFnProg):
    if tsk.id != ks.pg.similar:
        msg = f"[tsk] wrong triggerId[{tsk.id}]"
        lg.warn(msg)
        return nfy, now, msg

    thMin, thMax = tsk.args.get("thMin", 0.80), tsk.args.get("thMax", 0.99)

    try:
        asset = now.assets[0]

        onUpdate(1, "1%", f"preapre..")

        if not asset:
            msg = f"[tsk] assert not in now"
            nfy.error(msg)
            return nfy, now, msg
        if not isinstance(asset, models.Asset):
            msg = f"[tsk] the asset not is AssetType type[{type(asset)}]"
            nfy.error(msg)
            return nfy, now, msg

        onUpdate(5, "5%", f"Starting search with thresholds [{thMin:.2f}-{thMax:.2f}]")

        infos = db.vecs.findSimiliar(asset.id, thMin, thMax)

        for idx, info in enumerate(infos):
            aid, score = info.toTuple()
            lg.info(f"  no.{idx + 1}: ID[{aid}], score[{score:.6f}]")

        simIds = [ i.id for i in infos]

        onUpdate(80, "80%", f"Found {len(simIds)} similar photos")

        db.pics.setSimIds(asset.id, infos)

        assets = db.pics.getBy( simIds )

        now.assets.extend(assets)

        onUpdate(100, "100%", f"Completed finding similar photos for {asset.originalFileName}")

        msg = f"Found {len(simIds)} similar photos for {asset.originalFileName}"
        nfy.success(msg)



        return nfy, now, msg

    except Exception as e:
        msg = f"Similar photo search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        return nfy, now, msg

#========================================================================
# Set up global functions
#========================================================================
task.mapFns[ks.cmd.sim.find] = similar_FindSimilar
