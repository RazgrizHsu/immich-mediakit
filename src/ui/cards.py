from os import wait
from typing import List

from dash_bootstrap_components import ListGroup
from dsh import htm, dbc, dcc
from conf import ks, co
from util import log
from mod import models
import db

from ui import gvExif, gvExif

lg = log.get(__name__)

def mk(ass: models.Asset, modSim=True):
    if not ass: return htm.Div("Photo not found")

    imgSrc = f"/api/img/{ass.autoId}" if ass.id else None

    checked = False
    cssIds = "checked" if checked else ""

    exi = ass.jsonExif
    ex = ass.ex

    imgW = exi.exifImageWidth
    imgH = exi.exifImageHeight

    isMain = ass.vw.isMain
    isRels = ass.vw.isRelats
    isLvPh = ass.vdoId
    canFnd = ass.simOk is 0

    css = f"h-100 sim {cssIds} {'' if modSim else 'view'}"
    if isMain: css += " main"
    if isRels: css += " rels"

    tipExif = None
    if ass.jsonExif is not None:
        try:
            tipExif = gvExif.mkTipExif(ass.id, ass.jsonExif.toDict())
        except Exception as e:
            lg.error(f"Error processing EXIF data: {e}")

    return dbc.Card([
        dbc.CardHeader(
            htm.Div([
                dbc.Row([
                    dbc.Col(
                        dbc.Checkbox(label=f"#{ass.autoId}", value=False)
                    ),
                    dbc.Col(
                        [
                            htm.Span(f"Main", className="tag info lg ms-1")
                        ]
                        if isMain else
                        [
                            htm.Span("score:", className="tag sm info no-border"),
                            htm.Span(f"{ass.vw.score:.5f}", className="tag lg ms-1")
                        ]
                        if isRels else
                        [
                            htm.Span("score: ", className="tag sm second no-border"),
                            htm.Span(f"{ass.vw.score:.5f}", className="tag lg ms-1")
                        ]
                    )
                ])
            ], id={"type": "card-select", "id": ass.autoId}),
            className=f"p-2 curP"
        ) if modSim else None,
        htm.Div([

            htm.Div([
                htm.Video(
                    src=f"/api/livephoto/{ass.autoId}", loop=True, muted=True, autoPlay=True,
                    id={"type": "img-pop", "aid": ass.autoId}, n_clicks=0,
                    className="livephoto-video",
                ),
                htm.Img(
                    src=imgSrc,
                    id={"type": "img-pop", "aid": ass.autoId}, n_clicks=0,
                    className=f"card-img"
                ),
            ], className='view'),

            htm.Div([
                htm.Span(f"#{ass.autoId}", className="tag"),
                htm.Span(f"SimOK!", className="tag info") if ass.simOk else None,
            ], className="LT"),
            htm.Div([
                htm.Span(f"LivePhoto", className="tag blue livePhoto") if isLvPh else None,
                htm.Span([
                    htm.I(className='bi bi-images'),
                    f'{len(ex.albs)}'
                ], className='tag', **{}) if ex else None,

                htm.Span([
                    htm.I(className='bi bi-bookmark-check-fill'),
                    f'{len(ex.tags)}'
                ], className='tag') if ex else None,

                htm.Span([
                    htm.I(className='bi bi-person-bounding-box'),
                    f'{len(ex.tags)}'
                ], className='tag') if ex else None,
            ], className="RT"),
            htm.Div([
            ], className="LB"),
            htm.Div([

                htm.Span(f"{co.fmt.size(ass.jsonExif.fileSizeInByte)}", className="tag")
                if ass.jsonExif else None,
                htm.Span(f"{imgW} x {imgH}", className="tag lg"),
            ], className="RB")
        ], className="viewer"),
        dbc.CardBody([

            dbc.Row([
                htm.Span("id"), htm.Span(f"{ass.id}", className="tag"),
                htm.Span("device"), htm.Span(f"{ass.deviceId}", className="tag second txt-c"),
                htm.Span("FileName"), htm.Span(f"{ass.originalFileName}", className="tag second"),
                htm.Span("CreateAt"), htm.Span(f"{ass.fileCreatedAt}", className="tag second"),

                *([ htm.Span("livePhoto"), htm.Span(f"{ass.pathVdo}", className="tag blue"), ] if isLvPh else []),
                *([ htm.Span("live VdoId"), htm.Span(f"{ass.vdoId}", className="tag blue"), ] if isLvPh else []),

            ], class_name="grid"
            ) if db.dto.showGridInfo else None,
            htm.Div([
                tipExif,

                htm.Span('resolved ✅', className='tag') if ass.simOk else None,
                htm.Span('❤️', className='tag') if ass.isFavorite else None,
                htm.Span("exif", className='tag blue', id={'type':'exif-badge', 'index': ass.id}) if ass.jsonExif else None,
                #                dbc.Badge(
                #     "", color="danger", className="ms-1"
                # ) if isFav else None,
                # dbc.Badge(
                #     f"", color="secondary", className="ms-1"
                # ) if ass.simOk else None,
                #
                # htm.Span([
                #     htm.I(className='bi bi-images'),
                #     f'{len(ex.albs)}'
                # ], className='tag') if ex else None,
                #
                # htm.Span([
                #     htm.I(className='bi bi-bookmark-check-fill'),
                #     f'{len(ex.tags)}'
                # ], className='tag') if ex else None,
                #
                # htm.Span([
                #     htm.I(className='bi bi-person-bounding-box'),
                #     f'{len(ex.tags)}'
                # ], className='tag') if ex else None,


                # htm.Span(f'', className=''),


            ], className=f'tagbox'),

            # dbc.Row([
            #     htm.Table( htm.Tbody(gvExif.mkExifRows(ass)) , className="exif"),
            # ]) if db.dto.showGridInfo else None,

            htm.Div([


                dcc.Link(
                    f"Find Similar #{ass.autoId}",
                    href=f"/{ks.pg.similar}/{ass.autoId}",
                    className="btn btn-primary btn-sm w-76 me-2"
                ) if canFnd else None,


                dcc.Link(
                    htm.I(className='bi bi-trash'),
                    href=f"#{ass.autoId}",
                    className="btn btn-danger btn-sm w-20"
                ) if canFnd else None,

            ], className='m-2') if not modSim else None,


        ], className="p-0"),
    ], className=css)




def mkCardPnd(ass: models.Asset, showRelated=True):

    imgSrc = f"/api/img/{ass.autoId}" if ass.autoId else "assets/noimg.png"

    if not ass.id: return htm.Div("-No ass.id-")

    assId = ass.id

    checked = False
    cssIds = "checked" if checked else ""

    exi = ass.jsonExif

    imgW = exi.exifImageWidth if exi else 0
    imgH = exi.exifImageHeight if exi else 0

    htmSimInfos = []

    htmRelated = None
    if ass.vw.cntRelats and showRelated:
        rids = []

        htmRelated = [
            htm.Hr(className="my-2"),
            htm.Div([
                htm.Span("Related groups: ", className="text-muted"),
                htm.Span(f"{ass.vw.cntRelats}", className="badge bg-warning")
            ]),
            htm.Div(rids)
        ]

    return dbc.Card([
        htm.Div([
            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        "ViewGroup",
                        id={"type": "btn-view-group", "id": assId},
                        color="info",
                        size="sm",
                        className=""
                    )
                ),
                dbc.Col([
                    htm.Span("Matches: ", className="txt-sm"), htm.Span(f"{len(ass.simInfos) - 1}", className="tag lg ms-1 ps-2 pe-2")
                ], className="justify-content-end")
            ]
                , className="p-0")

        ], className="pt-2 ps-2 pb-3"),
        htm.Div([
            htm.Img(
                src=imgSrc,
                id={"type": "img-pop", "aid": ass.autoId}, n_clicks=0,
                className="card-img"
            ),
            htm.Div([
                htm.Span(f"#{ass.autoId}", className="tag sm second"),
            ], className="LB"),
            htm.Div([
                htm.Span(f"{imgW}", className="tag lg"),
                htm.Span("x"),
                htm.Span(f"{imgH}", className="tag lg"),
            ], className="RB")
        ], className="img"),
        dbc.CardBody([
            dbc.Row([
                htm.Span("id"), htm.Span(f"{ass.id}", className="badge bg-success text-truncate"),

            ], class_name="grid"),

            dbc.Row([
                htm.Span("fileName"), htm.Span(f"{ass.originalFileName}", className="text-truncate"),
                htm.Span("createAt"), htm.Span(f"{ass.fileCreatedAt}", className="text-truncate txt-sm"),

            ], class_name="grid2"),


            htm.Div(htmSimInfos),
            htm.Div(htmRelated),

        ], className="p-2")
    ], className=f"h-100 sim {cssIds}")

