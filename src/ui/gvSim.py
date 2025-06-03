from dsh import htm, dbc
from conf import co
from util import log
from mod import models
import db

lg = log.get(__name__)

from ui import gvExif

def mkGrid(assets: list[models.Asset], rootId: str, minW=230, maxW=300, onEmpty=None):
    if not assets or len(assets) == 0:
        if onEmpty:
            if isinstance(onEmpty, str):
                return dbc.Alert(f"{onEmpty}", color="warning", className="text-center")
            else:
                return onEmpty
        return htm.Div(dbc.Alert("--------", color="warning"), className="text-center")

    if not rootId:
        return htm.Div(dbc.Alert(f"non-rootId, assets:{assets}", color="warning"), className="text-center")

    rootSI = next((a.simInfos for a in assets if a.id == rootId), None)
    if not rootSI:
        msg = f"[mkGrid] no rootSI for rootId[ {rootId[:8]} ], ids: {[a.id[:8] for a in assets]}"
        lg.info(msg)
        return htm.Div(f"-- {msg} --")

    cntAss = len(assets)

    if cntAss <= 4:
        styGrid = {
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "1rem",
            "justifyContent": "center"
        }
        styItem = {"flex": f"1 1 {minW}px"}
    else:
        styGrid = {
            "display": "grid",
            "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
            "gap": "1rem"
        }
        styItem = {}

    rows = [htm.Div(mkCardSim(a, rootSI, isMain=(a.id == rootId)), style=styItem) for a in assets]

    lg.info(f"[sim:gv] assets[{len(assets)}] rows[{len(rows)}]")

    return htm.Div(rows, style=styGrid)


def mkCardSim(ass: models.Asset, srcSIs: list[models.SimInfo], isMain=False):
    if not ass: return htm.Div("Photo not found")

    imgSrc = f"/api/img/{ass.id}" if ass.id else None

    assId = ass.id
    fnm = ass.originalFileName
    dtc = ass.fileCreatedAt

    checked = ass.selected
    cssIds = "checked" if checked else ""

    si = next((i for i in srcSIs if i.id == ass.id), None) if srcSIs else None

    if not si:
        lg.error(f"[mkImgCardSim] asset:{ass}")
        return dbc.Alert(f"Not Found SimInfo #{ass.autoId} assetId[{assId}] in {srcSIs}", color="danger")

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
                    dbc.Col(
                        [
                            htm.Span(f"Main", className="tag info lg ms-1")
                        ]
                        if isMain else
                        [
                            htm.Span("score: ", className="tag sm second no-border"),
                            htm.Span(f"{si.score:.4f}", className="tag lg ms-1")
                        ]
                    )
                ])
            ], id={"type": "card-select", "id": assId}),
            className="p-2 curP"
        ),
        htm.Div([
            htm.Img(
                src=imgSrc,
                id={"type": "img-pop-multi", "id": ass.id, "autoId": ass.autoId}, n_clicks=0,
                className="card-img"
            ) if imgSrc else htm.Img(src="assets/noimg.png", className="card-img")
            ,
            htm.Div([
                htm.Span(f"#{ass.autoId} @{ass.simGID}", className="tag"),
            ]),
            htm.Div([

                htm.Span(f"{co.fmt.size(ass.jsonExif.fileSizeInByte)}", className="tag")
                if ass.jsonExif else None,
                htm.Span(f"{imgW} x {imgH}", className="tag lg"),
            ])
        ], className="img"),
        dbc.CardBody([

            dbc.Row([
                htm.Span("id"), htm.Span(f"{ass.id}", className="badge bg-success text-truncate"),
                htm.Span("FileName"), htm.Span(f"{ass.originalFileName}", className="text-truncate"),
                htm.Span("CreateAt"), htm.Span(f"{ass.fileCreatedAt}", className="text-truncate txt-sm"),

            ], class_name="grid2"
            ) if db.dto.showGridInfo else None,

            dbc.Row([
                htm.Table(
                    htm.Tbody(gvExif.mkExifRows(ass))
                    , className="exif"),
            ]) if db.dto.showGridInfo else None,

            dbc.Row(),

            # htm.Div([
            #     dbc.Button(
            #         "Details",
            #         id={"type": "details-btn", "id": assId},
            #         color="secondary",
            #         size="sm"
            #     )
            # ], className="d-flex justify-content-between align-items-center"),

        ], className="p-2"),
    ], className=cssClass)


# def mkRelatGroups(assets: list[models.Asset], minW=230, maxW=300):
#     styItem = {"maxWidth": f"{maxW}px"}
#     styGrid = {
#         "display": "grid",
#         "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
#         "gap": "1rem",
#         "justifyItems": "center"
#     }
#     cntAss = len(assets)
#     if cntAss <= 4:
#         styItem.pop("maxWidth")
#         styGrid.pop("justifyItems")
#
#     return htm.Div([
#         htm.Hr(className="my-4"),
#         htm.H5([
#             htm.Span("RelatGroups ", className=""),
#             htm.Span(f"({len(assets)})", className="badge bg-warning ms-2")
#         ], className="mb-3"),
#         # htm.Div([
#         #
#         #     mkGroupCard(rg) for rg in assets
#         #
#         # ], style=styGrid)
#     ])


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


def mkPndGrid(assets: list[models.Asset], minW=230, maxW=300, onEmpty=None):
    if not assets or len(assets) == 0:
        if onEmpty:
            if isinstance(onEmpty, str):
                return dbc.Alert(f"{onEmpty}", color="warning", className="text-center")
            else:
                return onEmpty
        return htm.Div(dbc.Alert("--------", color="warning"), className="text-center")

    cntAss = len(assets)

    if cntAss <= 4:
        styGrid = {
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "1rem",
            "justifyContent": "start"
        }
        styItem = {"flex": f"1 1 {minW}px", "maxWidth": f"{maxW}px"}
    else:
        styGrid = {
            "display": "grid",
            "gridTemplateColumns": f"repeat(auto-fit, minmax({minW}px, 1fr))",
            "gap": "1rem"
        }
        styItem = {}

    rows = [htm.Div(mkCardPnd(a), style=styItem) for a in assets]

    lg.info(f"[sim:gvPnd] assets[{len(assets)}] rows[{len(rows)}]")

    return htm.Div(rows, style=styGrid)


def mkCardPnd(ass: models.Asset, showRelated=True):
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

    htmRelated = None
    if hasattr(ass, 'relats') and ass.relats and showRelated:
        rids = []

        htmRelated = [
            htm.Hr(className="my-2"),
            htm.Div([
                htm.Span("Related groups: ", className="text-muted"),
                htm.Span(f"{ass.relats}", className="badge bg-warning")
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
                id={"type": "img-pop", "index": assId}, n_clicks=0,
                className="card-img"
            ),
            htm.Div([
                htm.Span(f"#{ass.autoId}", className="tag sm second"),
            ]),
            htm.Div([
                htm.Span(f"{imgW}", className="tag lg"),
                htm.Span("x"),
                htm.Span(f"{imgH}", className="tag lg"),
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


            htm.Div(htmSimInfos),
            htm.Div(htmRelated),

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
