from dsh import htm, dcc, dbc, inp, out, ste, cbk, noUpd

from util import log


lg = log.get(__name__)

from conf import ks, co
import db
from mod import models


class k:
    threshold = "thresholds"
    autoNext = "autoNext"
    showGridInfo = "showGridInfo"
    simIncRelGrp = "simIncRelGrp"
    simMaxDepths = "simMaxDepths"
    simMaxItems = "simMaxItems"

    cndGrpEnable = "cndGrpEnable"
    cndGrpSameDate = "cndGrpSameDate"
    cndGrpSameWidth = "cndGrpSameWidth"
    cndGrpSameHeight = "cndGrpSameHeight"
    cndGrpSameSize = "cndGrpSameSize"
    cndGrpMaxGroups = "cndGrpMaxGroups"

    cndGrpAuSel = "cndGrpAuSel"

    auSelEnable = "autoSelEnable"
    auSelSkipLowSim = "autoSelSkipLowSim"
    auSelAllLivePhoto = "auSelAllLivePhoto"

    auSelEarlier = "autoSelEarlier"
    auSelLater = "autoSelLater"
    auSelExifRicher = "autoSelExifRicher"
    auSelExifPoorer = "autoSelExifPoorer"
    auSelBiggerSize = "autoSelBiggerSize"
    auSelSmallerSize = "autoSelSmallerSize"
    auSelBiggerDimensions = "autoSelBiggerDimensions"
    auSelSmallerDimensions = "autoSelSmallerDimensions"
    auSelNameLonger = "autoSelNameLonger"
    auSelNameShorter = "autoSelNameShorter"



    @staticmethod
    def id(name): return {"type": "sets", "id": f"{name}"}


optMaxDepths = []
for i in range(6): optMaxDepths.append({"label": f"{i}", "value": i})

optMaxItems = [
    {"label": "100", "value": 100},
    {"label": "200", "value": 200},
    {"label": "300", "value": 300},
    {"label": "500", "value": 500},
    {"label": "1000", "value": 1000},
]

optMaxGroups = [
    {"label": "2", "value": 2},
    {"label": "5", "value": 5},
    {"label": "10", "value": 10},
    {"label": "20", "value": 20},
    {"label": "25", "value": 25},
    {"label": "50", "value": 50},
    {"label": "100", "value": 100},
]

optWeights = [
    {"label": "0", "value": 0},
    {"label": "1", "value": 1},
    {"label": "2", "value": 2},
    {"label": "3", "value": 3},
]

optThresholdMin = 0.5
optThresholdMarks = { "0.5":0.5, "0.6":0.6, "0.7": 0.7, "0.8": 0.8, "0.9": 0.9, "1": 1 }

def renderThreshold():
    return dbc.Card([
        dbc.CardHeader("Threshold Min & Max"),
        dbc.CardBody([
            htm.Div([
                htm.Div([
                    dcc.RangeSlider(
                        id=k.id(k.threshold), min=optThresholdMin, max=1, step=0.01, marks=optThresholdMarks, #type: ignore
                        value=[db.dto.simMin, db.dto.simMax],
                        tooltip={
                            "placement": "top", "always_visible": True,
                            "style": {"padding": "0 1px 0 1px", "fontSize": "11px"},
                        },
                    ),
                ], className=""),
                htm.Ul([
                    htm.Li("Thresholds set min/max similarity for image matching")
                ])
            ], className="irow mb-2"),
        ])
    ], className="mb-2")

def renderAutoSelect():
    return dbc.Card([
        dbc.CardHeader("Auto Selection"),
        dbc.CardBody([
            htm.Div([
                # Main enable switch
                dbc.Checkbox(id=k.id(k.auSelEnable), label="Enable", value=db.dto.auSelEnable), htm.Br(),

                dbc.Checkbox(id=k.id(k.auSelSkipLowSim), label="Skip has sim(<0.96) group", value=db.dto.auSel_SkipLowSim, disabled=not db.dto.auSelEnable),

                dbc.Checkbox(id=k.id(k.auSelAllLivePhoto), label="All LivePhotos (ignore criteria)", value=db.dto.auSel_AllLivePhoto, disabled=not db.dto.auSelEnable), htm.Br(),

                htm.Hr(),

                htm.Div([
                    htm.Span( htm.Span("DateTime", className="tag txt-smx me-1")),
                    htm.Label("Earlier", className="me-2"),
                    dbc.Select(id=k.id(k.auSelEarlier), options=optWeights, value=db.dto.auSel_Earlier, disabled=not db.dto.auSelEnable, size="sm", className="me-1"), #type:ignore
                    htm.Label("Later", className="me-2"),
                    dbc.Select(id=k.id(k.auSelLater), options=optWeights, value=db.dto.auSel_Later, disabled=not db.dto.auSelEnable, size="sm"), #type:ignore
                ], className="icriteria"),

                htm.Div([
                    htm.Span(htm.Span("Exif", className="tag txt-smx me-1")),
                    htm.Label("Richer", className="me-2"),
                    dbc.Select(id=k.id(k.auSelExifRicher), options=optWeights, value=db.dto.auSel_ExifRicher, disabled=not db.dto.auSelEnable, size="sm", className="me-1"), #type:ignore
                    htm.Label("Poorer", className="me-2"),
                    dbc.Select(id=k.id(k.auSelExifPoorer), options=optWeights, value=db.dto.auSel_ExifPoorer, disabled=not db.dto.auSelEnable, size="sm"), #type:ignore
                ], className="icriteria"),

                htm.Div([
                    htm.Span(htm.Span("Name Length", className="tag txt-smx me-1")),
                    htm.Label("Longer", className="me-2"),
                    dbc.Select(id=k.id(k.auSelNameLonger), options=optWeights, value=db.dto.auSel_NameLonger, disabled=not db.dto.auSelEnable, size="sm", className="me-1"), #type:ignore
                    htm.Label("Shorter", className="me-2"),
                    dbc.Select(id=k.id(k.auSelNameShorter), options=optWeights, value=db.dto.auSel_NameShorter, disabled=not db.dto.auSelEnable, size="sm"), #type:ignore
                ], className="icriteria"),

                htm.Div([
                    htm.Span(htm.Span("FileSize", className="tag txt-smx me-1")),
                    htm.Label("Bigger", className="me-2"),
                    dbc.Select(id=k.id(k.auSelBiggerSize), options=optWeights, value=db.dto.auSel_BiggerSize, disabled=not db.dto.auSelEnable, size="sm", className="me-1"), #type:ignore
                    htm.Label("Smaller", className="me-2"),
                    dbc.Select(id=k.id(k.auSelSmallerSize), options=optWeights, value=db.dto.auSel_SmallerSize, disabled=not db.dto.auSelEnable, size="sm"), #type:ignore
                ], className="icriteria"),

                htm.Div([
                    htm.Span(htm.Span("Dimensions", className="tag txt-smx me-1")),
                    htm.Label("Bigger", className="me-2"),
                    dbc.Select(id=k.id(k.auSelBiggerDimensions), options=optWeights, value=db.dto.auSel_BiggerDimensions, disabled=not db.dto.auSelEnable, size="sm", className="me-1"), #type:ignore
                    htm.Label("Smaller", className="me-2"),
                    dbc.Select(id=k.id(k.auSelSmallerDimensions), options=optWeights, value=db.dto.auSel_SmallerDimensions, disabled=not db.dto.auSelEnable, size="sm"), #type:ignore
                ], className="icriteria"),

                htm.Hr(),
                htm.Ul([
                    htm.Li("System auto-selects photo with highest total points based on criteria"),
                    htm.Li([htm.B("Points: "),"0=Ignore, 1=Low, 2=High priority"])
                ], className="text-muted small")
            ], className="mb-2 igrid txt-sm"),
        ])
    ], className="mb-0")


def renderCard():
    return dbc.Card([
        dbc.CardHeader("Similar Settings"),
        dbc.CardBody([
            htm.Div([
                htm.Label("Find Settings", className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id(k.autoNext), label="Auto Find Next", value=db.dto.autoNext),
                    dbc.Checkbox(id=k.id(k.showGridInfo), label="Show Grid Info", value=db.dto.showGridInfo),
                ], className="icbxs"),
                htm.Ul([
                    # htm.Li([htm.B(" "), ""])
                ])
            ], className="irow"),

            htm.Div([
                htm.Label("Related Settings", className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id(k.simIncRelGrp), label="Include Related", value=db.dto.simIncRelGrp),

                    htm.Div([
                        htm.Label("Max Depths: "),
                        dbc.Select(id=k.id(k.simMaxDepths), options=optMaxDepths, value=db.dto.simMaxDepths, className="")
                    ]),

                    htm.Div([
                        htm.Label("Max Items: "),
                        dbc.Select(id=k.id(k.simMaxItems), options=optMaxItems, value=db.dto.simMaxItems, className="") #type:ignore
                    ]),
                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Include Related: "), "Show all images in similarity group. Keep/Delete affects all displayed images"]),
                    htm.Li([htm.B("Max Depths: "), "Hierarchy levels to include in similarity search (0 = direct matches only)"]),
                    htm.Li([htm.B("Max Items: "), "Max images to process in similarity search to prevent UI slowdown"])
                ])
            ], className="irow"),

            htm.Div([
                htm.Label([
                    "Multiple Group",
                    htm.Span("Find groups of similar photos based on metadata", className="txt-smx text-muted ms-3")
                ], className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id(k.cndGrpEnable), label="Enable", value=db.dto.simCondGrpMode),

                    htm.Div([
                        htm.Label("Max Groups: "),
                        dbc.Select(id=k.id(k.cndGrpMaxGroups), options=optMaxGroups, value=db.dto.simCondMaxGroups, className="", disabled=True) #type:ignore
                    ]),

                    htm.Br(),

                    dbc.Checkbox(id=k.id(k.cndGrpSameDate), label="Same Date", value=db.dto.simCondSameDate, disabled=db.dto.simCondGrpMode),
                    dbc.Checkbox(id=k.id(k.cndGrpSameWidth), label="Same Width", value=db.dto.simCondSameWidth, disabled=db.dto.simCondGrpMode),
                    dbc.Checkbox(id=k.id(k.cndGrpSameHeight), label="Same Height", value=db.dto.simCondSameHeight, disabled=db.dto.simCondGrpMode),
                    dbc.Checkbox(id=k.id(k.cndGrpSameSize), label="Same File Size", value=db.dto.simCondSameSize, disabled=db.dto.simCondGrpMode),


                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Max Groups: "), "Maximum number of groups to return when grouping is enabled"]),
                    htm.Li([
                        htm.Span("⚠️ ", style={"color": "orange"}),
                        "Auto-mark unmatched photos as resolved to prevent re-searching. Use Clear Records to reset."
                    ])
                ])
            ], className="irow"),

        ])
    ], className="mb-0")


@cbk(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
        out(k.id(k.cndGrpSameDate), "disabled"),
        out(k.id(k.cndGrpSameWidth), "disabled"),
        out(k.id(k.cndGrpSameHeight), "disabled"),
        out(k.id(k.cndGrpSameSize), "disabled"),
        out(k.id(k.cndGrpMaxGroups), "disabled"),
    ],
    inp(k.id(k.threshold), "value"),
    inp(k.id(k.autoNext), "value"),
    inp(k.id(k.showGridInfo), "value"),
    inp(k.id(k.simIncRelGrp), "value"),
    inp(k.id(k.simMaxDepths), "value"),
    inp(k.id(k.simMaxItems), "value"),
    inp(k.id(k.cndGrpEnable), "value"),
    inp(k.id(k.cndGrpSameDate), "value"),
    inp(k.id(k.cndGrpSameWidth), "value"),
    inp(k.id(k.cndGrpSameHeight), "value"),
    inp(k.id(k.cndGrpSameSize), "value"),
    inp(k.id(k.cndGrpMaxGroups), "value"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def settings_OnUpd(ths, auNxt, shGdInfo, incRelGrp, maxDepths, maxItems, cndGrpEnable, cndGrpDate, cndGrpWidth, cndGrpHeight, cndGrpSize, maxGroups, dta_now):
    retNow = noUpd

    now = models.Now.fromDict(dta_now)
    mi, mx = ths

    db.dto.simMin = co.vad.float(mi, 0.93, 0.50, 0.99)
    db.dto.simMax = co.vad.float(mx, 1.00, 0.51, 1.00)

    db.dto.autoNext = auNxt
    db.dto.simMaxDepths = maxDepths
    db.dto.simMaxItems = maxItems

    db.dto.simCondGrpMode = cndGrpEnable
    db.dto.simCondSameDate = cndGrpDate
    db.dto.simCondSameWidth = cndGrpWidth
    db.dto.simCondSameHeight = cndGrpHeight
    db.dto.simCondSameSize = cndGrpSize
    db.dto.simCondMaxGroups = maxGroups

    # Control cndGrp enable/disable states
    cndGrpsDisabled = not cndGrpEnable
    maxGroupsDisabled = not cndGrpEnable

    def reloadAssets():
        nonlocal retNow, now
        lg.info(f"[sets:OnUpd] reload, incGroup[{db.dto.simIncRelGrp}] cndMode[{db.dto.simCondGrpMode}]")
        now.sim.assCur = db.pics.getSimAssets(now.sim.assAid, db.dto.simIncRelGrp if not db.dto.simCondGrpMode else False )
        retNow = now

    #now.sim.assCur = db.pics.getSimAssets(assId, db.dto.simIncRelGrp)

    if db.dto.showGridInfo != shGdInfo:
        db.dto.showGridInfo = shGdInfo
        if retNow == noUpd: reloadAssets()

    if db.dto.simIncRelGrp != incRelGrp:
        db.dto.simIncRelGrp = incRelGrp
        if retNow == noUpd: reloadAssets()

    # lg.info(f"[settings] changed: {ths}, {auNxt}, {shGdInfo}")

    return [retNow, cndGrpsDisabled, cndGrpsDisabled, cndGrpsDisabled, cndGrpsDisabled, maxGroupsDisabled]


@cbk(
    [
        out(k.id(k.auSelSkipLowSim), "disabled"),
        out(k.id(k.auSelAllLivePhoto), "disabled"),
        out(k.id(k.auSelEarlier), "disabled"),
        out(k.id(k.auSelLater), "disabled"),
        out(k.id(k.auSelExifRicher), "disabled"),
        out(k.id(k.auSelExifPoorer), "disabled"),
        out(k.id(k.auSelBiggerSize), "disabled"),
        out(k.id(k.auSelSmallerSize), "disabled"),
        out(k.id(k.auSelBiggerDimensions), "disabled"),
        out(k.id(k.auSelSmallerDimensions), "disabled"),
        out(k.id(k.auSelNameLonger), "disabled"),
        out(k.id(k.auSelNameShorter), "disabled"),
    ],
    inp(k.id(k.auSelEnable), "value"),
    inp(k.id(k.auSelSkipLowSim), "value"),
    inp(k.id(k.auSelAllLivePhoto), "value"),
    inp(k.id(k.auSelEarlier), "value"),
    inp(k.id(k.auSelLater), "value"),
    inp(k.id(k.auSelExifRicher), "value"),
    inp(k.id(k.auSelExifPoorer), "value"),
    inp(k.id(k.auSelBiggerSize), "value"),
    inp(k.id(k.auSelSmallerSize), "value"),
    inp(k.id(k.auSelBiggerDimensions), "value"),
    inp(k.id(k.auSelSmallerDimensions), "value"),
    inp(k.id(k.auSelNameLonger), "value"),
    inp(k.id(k.auSelNameShorter), "value"),
    prevent_initial_call=True
)
def autoSelect_OnUpd(enable, skipLo, onlyLive, earl, late, exRich, exPoor, szBig, szSml, dimBig, dimSml, namLong, namShor):
    db.dto.auSelEnable = enable
    db.dto.auSel_SkipLowSim = skipLo
    db.dto.auSel_AllLivePhoto = onlyLive
    db.dto.auSel_Earlier = earl
    db.dto.auSel_Later = late
    db.dto.auSel_ExifRicher = exRich
    db.dto.auSel_ExifPoorer = exPoor
    db.dto.auSel_BiggerSize = szBig
    db.dto.auSel_SmallerSize = szSml
    db.dto.auSel_BiggerDimensions = dimBig
    db.dto.auSel_SmallerDimensions = dimSml
    db.dto.auSel_NameLonger = namLong
    db.dto.auSel_NameShorter = namShor

    lg.info(f"[autoSel:OnUpd] Enable[{enable}] HighSim[{skipLo}] AlwaysPickLivePhoto[{onlyLive}] Earlier[{earl}] Later[{late}] ExifRich[{exRich}] ExifPoor[{exPoor}] BigSize[{szBig}] SmallSize[{szSml}] BigDim[{dimBig}] SmallDim[{dimSml}] NameLong[{namLong}] NameShort[{namShor}]")

    # Control enable/disable states
    dis = not enable

    return [dis, dis, dis, dis, dis, dis, dis, dis, dis, dis, dis, dis]
