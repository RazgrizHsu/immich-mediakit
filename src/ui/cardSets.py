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
    auSelEarly = "autoSelEarly"
    auSelExifMore = "autoSelExifMore"



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
    {"label": "5", "value": 5},
    {"label": "10", "value": 10},
    {"label": "20", "value": 20},
    {"label": "50", "value": 50},
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
                htm.Div([
                    htm.Div([
                        dbc.Checkbox(id=k.id(k.auSelEnable), label="Enable", value=db.dto.auSelEnable), htm.Br(),

                        dbc.Checkbox(id=k.id(k.auSelEarly), label="Early", value=db.dto.auSel_Early, disabled=db.dto.auSel_Early),
                        dbc.Checkbox(id=k.id(k.auSelExifMore), label="Early", value=db.dto.auSel_Exif_More, disabled=db.dto.auSel_Early),


                    ], className="icbxs"),
                    htm.Ul([
                        htm.Li([htm.B("Condition Group: "), "Search for multiple groups of similar photos that meet specific metadata conditions"]),
                        htm.Li([htm.B("Max Groups: "), "Maximum number of groups to return when grouping is enabled"]),
                    ])
                ], className="irow"),
                htm.Ul([
                    htm.Li("當搜尋結果出現後，自動選擇指定檔案")
                ])
            ], className="irow mb-2"),
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
