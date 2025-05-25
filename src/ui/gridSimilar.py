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


def createGrid(assets: list[models.Asset], rootId: str, minW=230, maxW=300, onEmpty=None):
    if not assets or len(assets) == 0:
        # lg.info( "[sim-grid] return empty grid" )
        if onEmpty:
            if isinstance(onEmpty, str):
                return dbc.Alert(f"{onEmpty}", color="warning", className="text-center")
            else:
                return onEmpty

        return htm.Div(
            dbc.Alert("--------", color="warning"),
            className="text-center"
        )

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

    rows = [htm.Div(mkImgCardSim(a, rootSI), className="photo-card", style=styItem) for a in assets]

    # lg.info( f"[sim-grid] create with rows[{len(assets)}] return rows[{len(rows)}]" )

    return htm.Div(rows, style=styGrid)


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


def create_base_photo_card(photo: models.Asset):
    if not photo: return htm.Div("Photo not found")

    thumbnail_path = photo.thumbnail_path
    preview_path = photo.preview_path
    fullsize_path = photo.fullsize_path

    image_path = thumbnail_path or preview_path or fullsize_path or ""

    photo_id = photo.id
    filename = photo.originalFileName
    created_date = photo.fileCreatedAt

    base_card_style = {"border": "3px solid #007bff", "box-shadow": "0 0 10px rgba(0, 123, 255, 0.5)"}

    return dbc.Card([
        dbc.CardHeader("Base Photo", className="text-center bg-primary text-white"),
        dbc.CardImg(
            src=f"{image_path}",
            top=True,
            style={"height": "250px", "objectFit": "contain"}
        ),
        dbc.CardBody([
            htm.H5(
                filename,
                className="card-title text-truncate",
                title=filename,
                style={"fontSize": "1rem"}
            ),
            htm.P(
                f"ID: {photo_id[:8]}...",
                className="card-text small",
                style={"fontSize": "0.8rem"}
            ),
            htm.P(
                created_date,
                className="card-text small",
                style={"fontSize": "0.8rem"}
            ),
            htm.Div([
                dbc.Button(
                    "Find Similar",
                    id={"type": "find-similar-btn", "id": photo_id},
                    color="primary",
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    "View",
                    color="info",
                    size="sm",
                    className="me-2",
                    href=fullsize_path,
                    target="_blank"
                ),
                dbc.Button(
                    "Details",
                    id={"type": "details-btn", "id": photo_id},
                    color="secondary",
                    size="sm"
                )
            ], className="d-flex justify-content-between")
        ], className="p-2")
    ],
        className="h-100", style=base_card_style
    )


def mkImgCardSim(ass: models.Asset, simInfos: list[models.SimInfo]):
    if not ass: return htm.Div("Photo not found")

    imgSrc = f"/api/img/{ass.id}" if ass.id else "assets/noimg.png"

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

    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(
                    dbc.Checkbox(
                        label="select", value=checked,
                        id={"type": "cbx-select", "id": assId},
                    )
                ),
                dbc.Col([
                    htm.Span("score: "), htm.Span(f"{si.score:.6f}", className="tag lg ms-1")
                ], className="d-flex justify-content-end")
            ])

        ], className=""),
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
