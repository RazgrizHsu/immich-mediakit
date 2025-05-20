import traceback
from typing import Optional

import db
from conf import ks
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd
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
    mthSim = "inp-sim-mth"

    btnFind = "btn-find-sim"
    btnClear = "btn-clear-sim"
    btnDel = "btn-delete-selected"

    pager = "div-pager"
    grid = "div-grid-sim"


# ========================================================================
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
                                dbc.Col(dbc.Alert(f"0", color="info", className="py-1 px-2 mb-2 text-center")),
                            ]),
                            dbc.Row([
                                dbc.Col(htm.Small("Unsearched", className="d-inline-block me-2"), width=5),
                                dbc.Col(dbc.Alert(f"0", color="info", className="py-1 px-2 mb-2 text-center")),
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
                                    dbc.Label("Similarity Method", className="txt-sm"),
                                    dcc.Dropdown(
                                        id=k.mthSim,
                                        options=[
                                            {"label": "Cosine Similarity", "value": "cosine"},
                                            {"label": "Euclidean Distance", "value": "euclidean"}
                                        ],
                                        value="cosine",
                                        clearable=False,
                                        className="mb-3"
                                    ),
                                ]),
                            ]),

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
                        ])
                    ], className="mb-0")
                ], width=8),
            ], className="mb-1"),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Find Similar",
                        id=k.btnFind,
                        color="primary",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),

                dbc.Col([
                    dbc.Button(
                        "Clear Results",
                        id=k.btnClear,
                        color="danger",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
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


            # Results container with tabs
            dbc.Tabs([
                dbc.Tab([
                    htm.Div([

                        dbc.Row([
                            dbc.Col([
                                dbc.Pagination(id=k.pager, active_page=7, min_value=1, max_value=99, first_last=True, previous_next=True, fully_expanded=False, style={"display": ""})
                            ], className="d-flex justify-content-center mb-3")
                        ]),

                        dbc.Spinner(
                            htm.Div(id=k.grid, className="mt-2"),
                            color="primary",
                            type="border",
                            spinner_style={"width": "3rem", "height": "3rem"}
                        )
                    ])
                ], label="Assets", tab_id="0"),
            ], active_tab="0"),

            dcc.Store(id=k.stoInitId, data=assetId)
        ]),
    ])

# ========================================================================
# todo (think):
# - when select assets equal 2, display pair compare view?
#     card = gvs.create_pair_card(
#         photo1_id=pair["photo1_id"],
#         photo2_id=pair["photo2_id"],
#         similarity=pair["similarity"],
#         index=i + 1,
#         selected_images=selected_images
#     )
# ========================================================================



# ========================================================================
# trigger modal
# ========================================================================
@callback(
    [
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    [
        inp(k.btnFind, "n_clicks"),
    ],
    [
        ste(k.slideTh, "value"),
        ste(k.mthSim, "value"),
        ste(ks.sto.now, "data"),
        ste(ks.sto.mdl, "data"),
        ste(ks.sto.tsk, "data"),
        ste(ks.sto.nfy, "data"),
    ],
    prevent_initial_call=True
)
def similar_RunModal(clk_fnd, thRange, mthSim, dta_now, dta_mdl, dta_tsk, dta_nfy):
    if not clk_fnd: return noUpd, noUpd, noUpd

    trgId = getTriggerId()

    now = models.Now.fromStore(dta_now)
    mdl = models.Mdl.fromStore(dta_mdl)
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)

    if tsk.id: return noUpd, noUpd, noUpd

    lg.info(f"[similar] trig[{trgId}] tsk[{tsk}]")

    if now.cntVec <= 0:
        nfy.error("No vector data to process")
        return mdl.toStore(), nfy.toStore(), noUpd

    thMin, thMax = thRange

    # 若有assetId
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
            lg.info(f"[sim] found non-simOk assetId[{ass.id}]")
            assId = ass.id

    if not asset:
        nfy.warn(f"[sim] not any asset to find..")
    else:
        mdl.reset()
        mdl.args = {'thMin': thMin, 'thMax': thMax}
        mdl.id = ks.pg.similar
        mdl.cmd = ks.cmd.sim.find
        mdl.msg = f"Begin finding similar with threshold[{thMin:.2f}-{thMax:.2f}] using {mthSim} method?"

    lg.info(f"[similar] modal[{mdl.id}] cmd[{mdl.cmd}] method[{mthSim}]")

    return mdl.toStore(), nfy.toStore(), now.toStore()


# ========================================================================
# task acts
# ========================================================================
def similar_FindSimilar(nfy: models.Nfy, now: models.Now, tsk: models.Tsk, onUpdate: task.IFnProg):
    if tsk.id != ks.pg.similar:
        msg = f"[tsk] wrong triggerId[{tsk.id}]"
        lg.warn(msg)
        return nfy, now, msg

    try:
        min_threshold = now.minThreshold if hasattr(now, 'minThreshold') else 0.9
        max_threshold = now.maxThreshold if hasattr(now, 'maxThreshold') else 0.99
        similarity_method = now.simMethod if hasattr(now, 'simMethod') else "cosine"
        base_photo_id = now.basePhotoId if hasattr(now, 'basePhotoId') else None

        onUpdate(5, "5%", f"Starting search with thresholds [{min_threshold:.2f}-{max_threshold:.2f}], method: {similarity_method}")

        asset_id = None

        if base_photo_id:
            lg.info(f"Using specified base photo id: {base_photo_id}")
            asset_id = base_photo_id
            onUpdate(10, "10%", f"Using specified base photo: {asset_id}")
        else:
            onUpdate(10, "10%", "Finding unprocessed asset")
            conn = db.pics.getConn()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM assets WHERE isVectored = 1 AND simOk = 0 LIMIT 1")
            row = cursor.fetchone()

            if not row:
                msg = "No unprocessed assets found"
                nfy.warn(msg)
                return nfy, now, msg

            asset_id = row[0]

        onUpdate(15, "15%", f"Processing asset {asset_id}")

        asset = db.pics.get(asset_id)
        if not asset:
            msg = f"Failed to get asset {asset_id}"
            nfy.error(msg)
            return nfy, now, msg

        onUpdate(30, "30%", f"Finding similar photos for {asset.originalFileName}")
        similar_photos = db.vecs.find_similar_photos(
            photo_id=asset_id,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            limit=100,
            similarity_method=similarity_method
        )

        similar_ids = [photo_id2 for photo_id1, photo_id2, score in similar_photos]
        onUpdate(80, "80%", f"Found {len(similar_ids)} similar photos")

        db.pics.setSimIds(asset_id, similar_ids)

        if not base_photo_id:
            conn = db.pics.getConn()
            cursor = conn.cursor()
            cursor.execute("UPDATE assets SET simOk = 1 WHERE id = ?", (asset_id,))
            conn.commit()

        onUpdate(100, "100%", f"Completed finding similar photos for {asset.originalFileName}")

        msg = f"Found {len(similar_ids)} similar photos for {asset.originalFileName}"
        nfy.success(msg)

        # 在now中傳回照片id及相似結果，以供後續使用
        now.lastSearchedId = asset_id
        now.similarPhotoCount = len(similar_ids)

        return nfy, now, msg

    except Exception as e:
        msg = f"Similar photo search failed: {str(e)}"
        nfy.error(msg)
        lg.error(traceback.format_exc())
        return nfy, now, msg

# ========================================================================
# Set up global functions
# ========================================================================
task.mapFns['similar_FindSimilar'] = similar_FindSimilar
