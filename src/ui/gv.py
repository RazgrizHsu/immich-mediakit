from dsh import htm, dcc, dbc
from conf import ks
from util import log
from mod import models
from ui.gvExif import mkTipExif

lg = log.get(__name__)


def createGrid(assets: list[models.Asset], minW: int = 250) -> htm.Div:
    if not assets or len(assets) == 0:
        return htm.Div(
            dbc.Alert("No photos match your filter criteria", color="warning"),
            className="text-center mt-4"
        )

    rows = [createPhotoCard(a) for a in assets]

    style = {
        "display": "grid",
        "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
        "gap": "1rem"
    }

    return htm.Div(rows, style=style)


def createPhotoCard(ass: models.Asset):
    hasVec = ass.isVectored == 1
    fnm = ass.originalFileName or '---'
    dtc = ass.fileCreatedAt or 'Unknown date'
    isFav = ass.isFavorite == 1
    assId = ass.id
    hasEx = ass.jsonExif is not None
    cantFind = ( ass.simOk == 1 ) or ass.simGIDs
    isLvPh = ass.vdoId is not None

    image_src = f"/api/img/{ass.autoId}" if ass.autoId else "assets/noimg.png"

    tipExif = None
    if hasEx and ass.jsonExif is not None:
        try:
            tipExif = mkTipExif(assId, ass.jsonExif.toDict())
        except Exception as e:
            lg.error(f"Error processing EXIF data: {e}")

    return htm.Div([
        htm.Div([
            htm.Video(
                src=f"/api/livephoto/{ass.autoId}", loop=True, muted=True, autoPlay=True,
                style={"height": "160px", "width": "100%", "objectFit": "cover", "cursor": "pointer"},
                className="livephoto-video",
            ) if isLvPh else
            dbc.CardImg(
                src=image_src,
                top=True,
                style={"height": "160px", "objectFit": "cover", "cursor": "pointer"},
            ),
            htm.Div([
                htm.Span(f"#{ass.autoId}", className="tag sm second"),
            ], className="LT"),
            htm.Div([
                htm.Span(f"LivePhoto", className="tag blue") if isLvPh else None,
            ], className="RT"),
        ],
            id={"type": "img-pop", "aid": ass.autoId}, n_clicks=0,
            className="head"
        ),
        htm.Div([
            htm.H6(
                fnm,
                className="text-truncate",
                title=fnm,
                style={"fontSize": "0.9rem"}
            ),
            htm.P(
                dtc,
                className="small",
                style={"fontSize": "0.8rem"}
            ),
            htm.Div([
                dbc.Badge(
                    "NoVec", color="warning", className="me-1"
                ) if not hasVec else None,
                dbc.Badge(
                    "❤️", color="danger", className="ms-1"
                ) if isFav else None,
                dbc.Badge(
                    f"resolved✅", color="secondary", className="ms-1"
                ) if ass.simOk else None,
                dbc.Badge(
                    "EXIF",
                    color="info",
                    className="me-1 exif-badge",
                    id={"type": "exif-badge", "index": assId}
                ) if hasEx else htm.Span(),


            ], className="d-flex flex-wrap"),

            tipExif,

            htm.Div([

                # dbc.Button(
                #     f"Find Similar #{ass.autoId}",
                #     id={"type": "btn-useAsAuid", "id": ass.autoId},
                #     color="primary",
                #     size="sm",
                #     className="w-100"
                # )

                dcc.Link(
                    f"Find Similar #{ass.autoId}",
                    href=f"/{ks.pg.similar}/{ass.autoId}",
                    className="btn btn-primary btn-sm w-100"
                ) if not cantFind else None

            ], className="mt-2") if not cantFind else None,

        ], className="p-2")
    ], className="img-card")
