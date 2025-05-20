from dsh import htm, dbc
from util import log, models

lg = log.get(__name__)


def createGrid_custom(photos: list[models.Asset], mkCol, photos_per_row: int = 4):
    if not photos or len(photos) == 0:
        return htm.Div(
            dbc.Alert("No photos match your filter criteria", color="warning"),
            className="text-center mt-4"
        )

    col_width = 12 // photos_per_row if 12 % photos_per_row == 0 else True

    rows = []
    row_photos = []
    for i, photo in enumerate(photos):
        row_photos.append(photo)
        if len(row_photos) == photos_per_row or i == len(photos) - 1:
            cols = []
            for idx, p in enumerate(row_photos):
                cols.append(dbc.Col(mkCol(p), width=col_width, className="mb-4"))
            rows.append(dbc.Row(cols, className="mb-2"))
            row_photos = []
    return htm.Div(rows)


def createGrid(assets: list[models.Asset], mkCol, minW: int = 250) -> htm.Div:
    if not assets or len(assets) == 0:
        return htm.Div(
            dbc.Alert("No photos match your filter criteria", color="warning"),
            className="text-center mt-4"
        )

    rows = [htm.Div(mkCol(a), className="photo-card") for a in assets]

    style = {
        "display": "grid",
        "grid-template-columns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem"
    }

    return htm.Div(rows, style=style)


def create_pair_card(photo1_id, photo2_id, similarity, index, selected_images=None):
    if selected_images is None:
        selected_images = []

    photo1 = db.pics.get(photo1_id)
    photo2 = db.pics.get(photo2_id)

    if not photo1 or not photo2:
        return htm.Div(f"Error loading photo details (IDs: {photo1_id}, {photo2_id})")

    return dbc.Card([
        dbc.CardHeader(f"Duplicate Pair #{index} - Similarity: {similarity:.4f}"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(create_photo_card(photo1, "Photo 1", photo1_id in selected_images), width=6),
                dbc.Col(create_photo_card(photo2, "Photo 2", photo2_id in selected_images), width=6),
            ])
        ])
    ], className="mb-3")


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


def create_photo_card(photo: models.Asset, label, is_selected=False):
    if not photo: return htm.Div("Photo not found")

    thumbnail_path = photo.thumbnail_path
    preview_path = photo.preview_path
    fullsize_path = photo.fullsize_path

    image_path = thumbnail_path or preview_path or fullsize_path or ""

    photo_id = photo.id
    filename = photo.originalFileName
    created_date = photo.fileCreatedAt

    card_style = {"border": "3px solid #28a745"} if is_selected else {}
    selection_text = "Selected ✓" if is_selected else "Not Selected"
    selection_class = "text-success fw-bold" if is_selected else "text-muted"
    button_color = "success" if is_selected else "primary"
    button_text = "Deselect" if is_selected else "Select"

    return dbc.Card([
        dbc.CardHeader(label),
        dbc.CardImg(
            src=image_path,
            top=True,
            style={"height": "200px", "objectFit": "contain"}
        ),
        dbc.CardBody([
            htm.H5(
                filename,
                className="card-title text-truncate",
                title=filename,
                style={"fontSize": "0.9rem"}
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
                htm.P(
                    selection_text,
                    className=f"card-text {selection_class}",
                    style={"fontSize": "0.8rem"}
                ),
                dbc.Button(
                    button_text,
                    id={"type": "select-btn", "id": photo_id},
                    color=button_color,
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
            ], className="d-flex justify-content-between align-items-center"),
        ], className="p-2")
    ], className="h-100", style=card_style)
