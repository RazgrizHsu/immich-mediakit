import dash.html as htm
import dash_bootstrap_components as dbc
from util import log, models
from ui.gridExif import createExifTooltip

lg = log.get(__name__)


def createGrid(assets: list[models.Asset], minW: int = 250) -> htm.Div:
    if not assets or len(assets) == 0:
        return htm.Div(
            dbc.Alert("No photos match your filter criteria", color="warning"),
            className="text-center mt-4"
        )

    rows = [htm.Div(createPhotoCard(a), className="photo-card") for a in assets]

    style = {
        "display": "grid",
        "grid-template-columns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem"
    }

    return htm.Div(rows, style=style)


def createPhotoCard(asset: models.Asset):
    hasVec = asset.isVectored == 1
    filename = asset.originalFileName or '---'
    created_date = asset.fileCreatedAt or 'Unknown date'
    is_favorite = asset.isFavorite == 1
    img_index = asset.id
    has_exif = asset.jsonExif is not None

    if asset.id:
        image_src = f"/api/img/{asset.id}"
    else:
        image_src = "assets/noimg.png"

    exif_tooltip = None
    if has_exif and asset.jsonExif is not None:
        try:
            exif_data = asset.jsonExif.toDict()
            exif_tooltip = createExifTooltip(img_index, exif_data)
        except Exception as e:
            lg.error(f"Error processing EXIF data: {e}")

    return dbc.Card([
        htm.Div([
            dbc.CardImg(
                src=image_src,
                top=True,
                style={"height": "160px", "objectFit": "cover", "cursor": "pointer"},
            )
        ], id={"type": "img-pop", "index": img_index}, n_clicks=0),
        dbc.CardBody([
            htm.H6(
                filename,
                className="text-truncate",
                title=filename,
                style={"fontSize": "0.9rem"}
            ),
            htm.P(
                created_date,
                className="small",
                style={"fontSize": "0.8rem"}
            ),
            htm.Div([
                dbc.Badge(
                    "VecOk", color="success", className="me-1"
                ) if hasVec else dbc.Badge(
                    "NoVec", color="warning", className="me-1"
                ),
                dbc.Badge(
                    "EXIF",
                    color="info",
                    className="me-1 exif-badge",
                    id={"type": "exif-badge", "index": img_index}
                ) if has_exif else htm.Span(),
                dbc.Badge(
                    "❤️", color="danger", className="ms-1"
                ) if is_favorite else htm.Span(),
            ], className="d-flex flex-wrap"),
            exif_tooltip
        ], className="p-2")
    ], className="h-100 photo-card")
