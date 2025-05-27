from dsh import htm, dbc
from util import log
from mod import models

lg = log.get(__name__)


# def _Grid_RowCols(photos: list[models.Asset], mkCol, photos_per_row: int = 4):
#     if not photos or len(photos) == 0:
#         return htm.Div(
#             dbc.Alert("No photos match your filter criteria", color="warning"),
#             className="text-center mt-4"
#         )
#     col_width = 12 // photos_per_row if 12 % photos_per_row == 0 else True
#     rows = []
#     row_photos = []
#     for i, photo in enumerate(photos):
#         row_photos.append(photo)
#         if len(row_photos) == photos_per_row or i == len(photos) - 1:
#             cols = []
#             for idx, p in enumerate(row_photos):
#                 cols.append(dbc.Col(mkCol(p), width=col_width, className="mb-4"))
#             rows.append(dbc.Row(cols, className="mb-2"))
#             row_photos = []
#     return htm.Div(rows)


def mkGrid(assets: list[models.Asset], rootId: str, minW=230, maxW=300, onEmpty=None):
    if not assets or len(assets) == 0:
        # lg.info( "[sim:gv] return empty grid" )
        if onEmpty:
            if isinstance(onEmpty, str):
                return dbc.Alert(f"{onEmpty}", color="warning", className="text-center")
            else:
                return onEmpty

        return htm.Div(dbc.Alert("--------", color="warning"), className="text-center")

    rootSI = next((a.simInfos for a in assets if a.id == rootId), None)

    styItem = {"maxWidth": f"{maxW}px"}
    styGrid = {
        "display": "grid",
        "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem",
        "justifyItems": "center"
    }

    cntAss = len(assets)
    if cntAss <= 4:
        styItem.pop("maxWidth")
        styGrid.pop("justifyItems")

    rows = [htm.Div(mkImgCardSim(a, rootSI, isMain=(a.id == rootId)), className="photo-card", style=styItem) for a in assets]

    lg.info(f"[sim:gv] assets[{len(assets)}] rows[{len(rows)}]")

    layout = [htm.Div(rows, style=styGrid)]

    return htm.Div(layout)

def mkRelatGroups(assets: list[models.Asset], minW=230, maxW=300):
    styItem = {"maxWidth": f"{maxW}px"}
    styGrid = {
        "display": "grid",
        "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem",
        "justifyItems": "center"
    }
    cntAss = len(assets)
    if cntAss <= 4:
        styItem.pop("maxWidth")
        styGrid.pop("justifyItems")

    return htm.Div([
        htm.Hr(className="my-4"),
        htm.H5([
            htm.Span("Related Groups ", className=""),
            htm.Span(f"({len(assets)})", className="badge bg-warning ms-2")
        ], className="mb-3"),
        htm.Div([

            mkGroupCard(rg) for rg in assets

        ], style=styGrid)
    ])


def mkGroupCard(ass: models.Asset):
    return dbc.Card([
        dbc.CardHeader([
            htm.Div([
                htm.Span(f"#{ass.autoId} - {ass.originalFileName}", className="text-truncate"),
                dbc.Button(
                    "View Group",
                    id={"type": "btn-view-group", "id": ass.id},
                    color="primary",
                    size="sm",
                    className="float-end"
                )
            ], className="d-flex justify-content-between align-items-center")
        ], className="py-2"),
        dbc.CardBody([
            # 顯示群組中的所有照片縮圖
            htm.Div([
                # 左側主圖
                htm.Div([
                    htm.Div([
                        htm.Img(
                            src=f"/api/img/{ass.id}" if ass.id else "assets/noimg.png",
                            className="img-thumbnail",
                            style={"height": "120px", "width": "120px", "objectFit": "cover"},
                            title=f"#{ass.autoId} - {ass.originalFileName}"
                        ),
                        htm.Span("Main", className="badge bg-warning position-absolute",
                                 style={"top": "5px", "left": "5px"})
                    ], className="position-relative")
                ], className="me-3"),

                # 右側次圖網格
                htm.Div([
                    htm.Div([
                        # 顯示前7張次圖
                        *[
                            htm.Div([
                                htm.Img(
                                    src=f"/api/img/{si.id}",
                                    className="img-thumbnail",
                                    style={"height": "60px", "width": "60px", "objectFit": "cover"},
                                ),
                                htm.Span(
                                    f"{si.score:.3f}",
                                    className="badge bg-info position-absolute",
                                    style={"bottom": "2px", "right": "2px", "fontSize": "10px", "padding": "2px 4px"}
                                )
                            ], className="position-relative")
                            for si in (ass.simInfos[1:8] if len(ass.simInfos) > 1 else [])
                        ],
                        # 如果超過8張（1主圖+7次圖），第8格顯示更多提示
                        htm.Div([
                            htm.Span(
                                f"...{len(ass.simInfos) - 8} more",
                                className="text-muted",
                                style={"fontSize": "11px", "fontWeight": "bold"}
                            )
                        ], className="d-flex align-items-center justify-content-center",
                            style={"height": "60px", "width": "60px", "backgroundColor": "#2a2a2a", "borderRadius": "4px"})
                        if len(ass.simInfos) > 8 else None
                    ], style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(4, 1fr)",
                        "gap": "0.25rem"
                    })
                ], className="flex-grow-1")
            ], className="d-flex align-items-start"),
            htm.Hr(className="my-2"),
            htm.Div([
                htm.Small([
                    htm.Span("Photos in group: ", className="text-muted"),
                    htm.Span(f"{len(ass.groupAssets) if hasattr(ass, 'groupAssets') else 0}", className="badge bg-info me-2")
                ]),
                htm.Small([
                    htm.Span("Similarity range: ", className="text-muted"),
                    htm.Span(
                        f"{min(s.score for s in ass.simInfos if s.score):.3f} - {max(s.score for s in ass.simInfos if s.score):.3f}"
                        if ass.simInfos and any(s.score for s in ass.simInfos)
                        else "N/A",
                        className="badge bg-secondary"
                    )
                ])
            ], className="d-flex justify-content-between")
        ], className="p-2")
    ], className="h-100 related-group")


def mkPndGrid(assets: list[models.Asset], minW=230, maxW=300, onEmpty=None, showRelated=True):
    if not assets or len(assets) == 0:
        # lg.info( "[sim:gv] return empty grid" )
        if onEmpty:
            if isinstance(onEmpty, str):
                return dbc.Alert(f"{onEmpty}", color="warning", className="text-center")
            else:
                return onEmpty

        return htm.Div(dbc.Alert("--------", color="warning"), className="text-center")

    styItem = {"maxWidth": f"{maxW}px"}
    styGrid = {
        "display": "grid",
        "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem",
        "justifyItems": "center"
    }

    cntAss = len(assets)
    if cntAss <= 4:
        styItem.pop("maxWidth")
        styGrid.pop("justifyItems")

    try:
        rows = [htm.Div(mkImgCardPending(a, showRelated), className="photo-card", style=styItem) for a in assets]

        # lg.info( f"[sim:gv] mkPndGrid with assets[{len(assets)}] return rows[{len(rows)}]" )

        return htm.Div(rows, style=styGrid)
    except Exception as e:
        lg.error(f"[mkPndGrid] Render failed, assets[{assets}], {e}", exc_info=True)


# def create_pair_card(photo1_id, photo2_id, similarity, index, selected_images=None):
#     if selected_images is None:
#         selected_images = []
#
#     photo1 = db.pics.get(photo1_id)
#     photo2 = db.pics.get(photo2_id)
#
#     if not photo1 or not photo2:
#         return htm.Div(f"Error loading photo details (IDs: {photo1_id}, {photo2_id})")
#
#     return dbc.Card([
#         dbc.CardHeader(f"Duplicate Pair #{index} - Similarity: {similarity:.4f}"),
#         dbc.CardBody([
#             dbc.Row([
#                 dbc.Col(create_photo_card(photo1, "Photo 1", photo1_id in selected_images), width=6),
#                 dbc.Col(create_photo_card(photo2, "Photo 2", photo2_id in selected_images), width=6),
#             ])
#         ])
#     ], className="mb-3")


def mkImgCardSim(ass: models.Asset, simInfos: list[models.SimInfo], isMain=False):
    if not ass: return htm.Div("Photo not found")

    imgSrc = f"/api/img/{ass.id}" if ass.id else None

    assId = ass.id
    fnm = ass.originalFileName
    dtc = ass.fileCreatedAt

    checked = ass.selected
    cssIds = "checked" if checked else ""

    si = next((i for i in simInfos if i.id == ass.id), None) if simInfos else None

    if not si:
        return dbc.Alert(f"Photo assetId[{assId}] SimNotFound not found", color="danger")

    exi = ass.jsonExif

    imgW = exi.exifImageWidth
    imgH = exi.exifImageHeight

    cssClass = f"h-100 sim {cssIds}"
    if isMain:
        cssClass += " main"

    return dbc.Card([
        dbc.CardHeader(
            htm.Div([
                dbc.Row([
                    dbc.Col(
                        dbc.Checkbox(label=f"#{ass.autoId}", value=checked)
                    ),
                    dbc.Col([
                                htm.Span(f"Main", className="tag info lg ms-1")
                            ] if isMain else
                            [
                                htm.Span("score: "),
                                htm.Span(f"{si.score:.6f}", className="tag lg ms-1")
                            ]

                            , className="d-flex justify-content-end")
                ])
            ], id={"type": "card-select", "id": assId}),
            className="p-2 curP"
        ),
        htm.Div([
            htm.Img(
                src=imgSrc,
                id={"type": "img-pop-multi", "id": ass.id, "autoId": ass.autoId }, n_clicks=0,
                className="card-img"
            ) if imgSrc else htm.Img(src="assets/noimg.png", className="card-img")
            ,
            htm.Div([
                htm.Span(f"#{ass.autoId}", className="badge"),
            ]),
            htm.Div([
                htm.Span(f"{imgW}", className="badge bg-primary"),
                htm.Span("x"),
                htm.Span(f"{imgH}", className="badge bg-primary"),
            ])
        ], className="img"),
        dbc.CardBody([
            dbc.Row([
                htm.Span("id"), htm.Span(f"{ass.id}", className="badge bg-success text-truncate"),

            ], class_name="grid"),

            dbc.Row([
                htm.Span("fileName"), htm.Span(f"{ass.originalFileName}", className="text-truncate"),
                htm.Span("createAt"), htm.Span(f"{ass.fileCreatedAt}", className="text-truncate txt-sm"),

            ], class_name="grid2"),

            # htm.Div([
            #     dbc.Button(
            #         "Details",
            #         id={"type": "details-btn", "id": assId},
            #         color="secondary",
            #         size="sm"
            #     )
            # ], className="d-flex justify-content-between align-items-center"),

        ], className="p-2")
    ], className=cssClass)


def mkImgCardPending(ass: models.Asset, showRelated=True):
    if not ass: return htm.Div("Photo not found")

    imgSrc = f"/api/img/{ass.id}" if ass.id else "assets/noimg.png"

    if not ass.id:
        return htm.Div("-Render None-")

    assId = ass.id
    fnm = ass.originalFileName
    dtc = ass.fileCreatedAt

    checked = ass.selected
    cssIds = "checked" if checked else ""

    exi = ass.jsonExif

    imgW = exi.exifImageWidth if exi else 0
    imgH = exi.exifImageHeight if exi else 0

    htmSimInfos = []

    # for si in ass.simInfos:
    #     if not si.isSelf:
    #         htmSimInfos.append(htm.Div([
    #             htm.Span(f"score[{si.score:.6f}]", className="tag"),
    #             htm.Span(f"{si.id[:8]}...", className="badge bg-primary txt-sm"),
    #         ]))

    # 顯示相關群組
    htmRelated = []
    if hasattr(ass, 'relats') and ass.relats and showRelated:
        htmRelated.append(htm.Hr(className="my-2"))
        htmRelated.append(htm.Div([
            htm.Span("Related groups: ", className="text-muted"),
            htm.Span(f"{len(ass.relats)}", className="badge bg-warning")
        ]))
        for ra in ass.relats[:2]:
            htmRelated.append(htm.Div([
                htm.Span(f"#{ra.autoId}", className="badge bg-secondary me-1"),
                htm.Span(f"{ra.id[:8]}...", className="text-muted small"),
            ]))
        if len(ass.relats) > 2:
            htmRelated.append(htm.Div(
                f"... {len(ass.relats) - 2} more",
                className="text-muted small"
            ))

    return dbc.Card([
        htm.Div([
            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        "View as Group",
                        id={"type": "btn-view-group", "id": assId},
                        color="info",
                        size="sm",
                        className="w-100"
                    )
                ),
                dbc.Col([
                    htm.Span("Matches: ", className="txt-sm"), htm.Span(f"{len(ass.simInfos) - 1}", className="tag lg ms-1")
                ], className="justify-content-end")
            ]
                , className="p-0")

        ], className="pt-2 ps-2 pb-3"),
        htm.Div([
            htm.Img(
                src=imgSrc,
                id={"type": "img-pop", "index": assId}, n_clicks=0,
                className="card-img"
            ),
            htm.Div([
                htm.Span(f"#{ass.autoId}", className="badge"),
            ]),
            htm.Div([
                htm.Span(f"{imgW}", className="badge bg-primary"),
                htm.Span("x"),
                htm.Span(f"{imgH}", className="badge bg-primary"),
            ])
        ], className="img"),
        dbc.CardBody([
            dbc.Row([
                htm.Span("id"), htm.Span(f"{ass.id}", className="badge bg-success text-truncate"),

            ], class_name="grid"),

            dbc.Row([
                htm.Span("fileName"), htm.Span(f"{ass.originalFileName}", className="text-truncate"),
                htm.Span("createAt"), htm.Span(f"{ass.fileCreatedAt}", className="text-truncate txt-sm"),

            ], class_name="grid2"),


            htm.Div(
                htmSimInfos + htmRelated,
            ),

            # htm.Div([
            #     dbc.Button(
            #         "Details",
            #         id={"type": "details-btn", "id": assId},
            #         color="secondary",
            #         size="sm"
            #     )
            # ], className="d-flex justify-content-between align-items-center"),

        ], className="p-2")
    ], className=f"h-100 sim {cssIds}")
