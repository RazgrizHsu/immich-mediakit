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
    auSelHighSimilarity = "autoSelHighSimilarity"

    auSelEarlier = "autoSelEarlier"
    auSelLater = "autoSelLater"
    auSelExifRicher = "autoSelExifRicher"
    auSelExifPoorer = "autoSelExifPoorer"
    auSelBiggerSize = "autoSelBiggerSize"
    auSelSmallerSize = "autoSelSmallerSize"
    auSelBiggerDimensions = "autoSelBiggerDimensions"
    auSelSmallerDimensions = "autoSelSmallerDimensions"



    @staticmethod
    def id(name):
        return {"type": "sets", "id": f"{name}"}


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

optThresholdMarks = { "0.6":0.6, "0.7": 0.7, "0.8": 0.8, "0.9": 0.9, "1": 1 }

def renderThreshold():
    return dbc.Card([
        dbc.CardHeader("Threshold Min & Max"),
        dbc.CardBody([
            htm.Div([
                htm.Div([
                    dcc.RangeSlider(
                        id=k.id(k.threshold), min=0.6, max=1, step=0.01, marks=optThresholdMarks, #type: ignore
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
        dbc.CardHeader("Auto Select"),
        dbc.CardBody([
            htm.Div([
                # Main enable switch
                dbc.Checkbox(id=k.id(k.auSelEnable), label="Enable Auto Selection", value=db.dto.auSelEnable),
                htm.Br(),

                # High similarity filter
                dbc.Checkbox(id=k.id(k.auSelHighSimilarity), label="Skip low similarity (<0.96)",
                           value=db.dto.auSel_HighSimilarity, disabled=not db.dto.auSelEnable),
                htm.Hr(),

                htm.H6("Selection Criteria", className="mb-2"),

                # Point selection grid
                htm.Small("DateTime:", className="text-muted mb-2"),

                dbc.Row([
                    dbc.Col([
                        htm.Label("Earlier", className="me-2"),
                        dbc.Select(id=k.id(k.auSelEarlier), options=optWeights, value=db.dto.auSel_Earlier, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                    dbc.Col([
                        htm.Label("Later", className="me-2"),
                        dbc.Select(id=k.id(k.auSelLater), options=optWeights, value=db.dto.auSel_Later, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                ], className="mb-2"),

                htm.Small("Exif:", className="text-muted mb-2"),
                dbc.Row([
                    dbc.Col([
                        htm.Label("Richer", className="me-2"),
                        dbc.Select(id=k.id(k.auSelExifRicher), options=optWeights, value=db.dto.auSel_ExifRicher, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                    dbc.Col([
                        htm.Label("Poorer", className="me-2"),
                        dbc.Select(id=k.id(k.auSelExifPoorer), options=optWeights, value=db.dto.auSel_ExifPoorer, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                ], className="mb-2"),

                htm.Small("FileSize:", className="text-muted mb-2"),
                dbc.Row([
                    dbc.Col([
                        htm.Label("Bigger", className="me-2"),
                        dbc.Select(id=k.id(k.auSelBiggerSize), options=optWeights, value=db.dto.auSel_BiggerSize, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                    dbc.Col([
                        htm.Label("Smaller", className="me-2"),
                        dbc.Select(id=k.id(k.auSelSmallerSize), options=optWeights, value=db.dto.auSel_SmallerSize, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                ], className="mb-2"),

                htm.Small("Dimensions (Width+Height):", className="text-muted mb-2"),
                dbc.Row([
                    dbc.Col([
                        htm.Label("Bigger", className="me-2"),
                        dbc.Select(id=k.id(k.auSelBiggerDimensions), options=optWeights, value=db.dto.auSel_BiggerDimensions, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                    dbc.Col([
                        htm.Label("Smaller", className="me-2"),
                        dbc.Select(id=k.id(k.auSelSmallerDimensions), options=optWeights, value=db.dto.auSel_SmallerDimensions, disabled=not db.dto.auSelEnable, size="sm") #type:ignore
                    ], width=6),
                ], className="mb-2"),

                htm.Hr(),
                htm.Ul([
                    htm.Li("System calculates points for each photo based on criteria"),
                    htm.Li("Photo with highest total points gets auto-selected"),
                    htm.Li("Points: 0=Not considered, 1=Low priority, 2=High priority")
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
                    htm.Li([htm.B("Include Related: "), "Display all images in the similarity group (not just direct matches). All displayed images will be affected by Keep/Delete operations"]),
                    htm.Li([htm.B("Max Depths: "), "During Find Similar, how many levels of hierarchical relationships to include in the same group (0 = direct matches only)"]),
                    htm.Li([htm.B("Max Items: "), "Maximum number of images to process during similarity search to prevent UI slowdown"])
                ])
            ], className="irow"),

            htm.Div([
                htm.Label("Condition Group", className="txt-sm"),
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
                    htm.Li([htm.B("Condition Group: "), "Search for multiple groups of similar photos that meet specific metadata conditions"]),
                    htm.Li([htm.B("Max Groups: "), "Maximum number of groups to return when grouping is enabled"]),
                    htm.Li([
                        htm.Span("⚠️ ", style={"color": "orange"}),
                        htm.B("Important: ", style={"color": "red"}),
                        "When enabled, any photos that don't meet group conditions will be automatically marked as resolved to prevent re-searching. Use Clear All Records to reset if needed."
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

    lg.info(f"[sets:OnUpd] cndGrpEnable[{cndGrpEnable}]")

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
        out(k.id(k.auSelHighSimilarity), "disabled"),
        out(k.id(k.auSelEarlier), "disabled"),
        out(k.id(k.auSelLater), "disabled"),
        out(k.id(k.auSelExifRicher), "disabled"),
        out(k.id(k.auSelExifPoorer), "disabled"),
        out(k.id(k.auSelBiggerSize), "disabled"),
        out(k.id(k.auSelSmallerSize), "disabled"),
        out(k.id(k.auSelBiggerDimensions), "disabled"),
        out(k.id(k.auSelSmallerDimensions), "disabled"),
    ],
    inp(k.id(k.auSelEnable), "value"),
    inp(k.id(k.auSelHighSimilarity), "value"),
    inp(k.id(k.auSelEarlier), "value"),
    inp(k.id(k.auSelLater), "value"),
    inp(k.id(k.auSelExifRicher), "value"),
    inp(k.id(k.auSelExifPoorer), "value"),
    inp(k.id(k.auSelBiggerSize), "value"),
    inp(k.id(k.auSelSmallerSize), "value"),
    inp(k.id(k.auSelBiggerDimensions), "value"),
    inp(k.id(k.auSelSmallerDimensions), "value"),
    prevent_initial_call=True
)
def autoSelect_OnUpd(auSelEnable, auSelHighSimilarity, auSelEarlier, auSelLater, auSelExifRicher, auSelExifPoorer, auSelBiggerSize, auSelSmallerSize, auSelBiggerDimensions, auSelSmallerDimensions):
    db.dto.auSelEnable = auSelEnable
    db.dto.auSel_HighSimilarity = auSelHighSimilarity
    db.dto.auSel_Earlier = auSelEarlier
    db.dto.auSel_Later = auSelLater
    db.dto.auSel_ExifRicher = auSelExifRicher
    db.dto.auSel_ExifPoorer = auSelExifPoorer
    db.dto.auSel_BiggerSize = auSelBiggerSize
    db.dto.auSel_SmallerSize = auSelSmallerSize
    db.dto.auSel_BiggerDimensions = auSelBiggerDimensions
    db.dto.auSel_SmallerDimensions = auSelSmallerDimensions

    lg.info(f"[autoSel:OnUpd] Enable[{auSelEnable}] HighSim[{auSelHighSimilarity}] Earlier[{auSelEarlier}] Later[{auSelLater}] ExifRich[{auSelExifRicher}] ExifPoor[{auSelExifPoorer}] BigSize[{auSelBiggerSize}] SmallSize[{auSelSmallerSize}] BigDim[{auSelBiggerDimensions}] SmallDim[{auSelSmallerDimensions}]")

    # Control enable/disable states
    subOptionsDisabled = not auSelEnable

    return [subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled, subOptionsDisabled]
