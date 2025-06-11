from dsh import htm, dcc, dbc, inp, out, ste, cbk, noUpd

from util import log


lg = log.get(__name__)

from conf import ks, co
import db
from mod import models


class k:
    ths = "thresholds"
    autoNxt = "autoNext"
    shGdInfo = "showGridInfo"
    simIncRelGrp = "simIncRelGrp"
    simMaxDepths = "simMaxDepths"
    simMaxItems = "simMaxItems"
    filterSameDate = "filterSameDate"
    filterSameWidth = "filterSameWidth"
    filterSameHeight = "filterSameHeight"
    filterSameSize = "filterSameSize"
    filterMaxGroups = "filterMaxGroups"
    filterEnable = "filterEnable"

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


def renderCard():
    return dbc.Card([
        dbc.CardHeader("Similar Settings"),
        dbc.CardBody([
            htm.Div([
                htm.Label("Threshold Min & Max", className="txt-sm"),
                htm.Div([
                    dcc.RangeSlider(
                        id=k.id(k.ths), min=0.5, max=1, step=0.01, marks=ks.defs.thMarks, #type: ignore
                        value=[db.dto.simMin, db.dto.simMax],
                        tooltip={
                            "placement": "top", "always_visible": True,
                            "style": {"padding": "1px 3px 1px 3px", "fontSize": "13px"},
                        },
                    ),
                ], className=""),
                htm.Ul([
                    htm.Li("Thresholds set min/max similarity for image matching")
                ])
            ], className="irow"),

            htm.Div([
                htm.Label("Find Settings", className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id(k.autoNxt), label="Auto Find Next", value=db.dto.autoNext),
                    dbc.Checkbox(id=k.id(k.shGdInfo), label="Show Grid Info", value=db.dto.showGridInfo),
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
                        dbc.Select(id=k.id(k.simMaxItems), options=optMaxItems, value=db.dto.simMaxItems, className="") #type: ignore
                    ]),
                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Include Related: "), "Display all images in the similarity group (not just direct matches). All displayed images will be affected by Keep/Delete operations"]),
                    htm.Li([htm.B("Max Depths: "), "During Find Similar, how many levels of hierarchical relationships to include in the same group (0 = direct matches only)"]),
                    htm.Li([htm.B("Max Items: "), "Maximum number of images to process during similarity search to prevent UI slowdown"])
                ])
            ], className="irow"),

            htm.Div([
                htm.Label("Condition Group Search", className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id("filterEnable"), label="Enable", value=db.dto.simModeCondGrp),

                    htm.Div([
                        htm.Label("Max Groups: "),
                        dbc.Select(id=k.id(k.filterMaxGroups), options=optMaxGroups, value=db.dto.simFilterMaxGroups, className="", disabled=True) #type:ignore
                    ]),

                    htm.Br(),

                    dbc.Checkbox(id=k.id(k.filterSameDate), label="Same Date", value=db.dto.simFilterSameDate, disabled=db.dto.simModeCondGrp),
                    dbc.Checkbox(id=k.id(k.filterSameWidth), label="Same Width", value=db.dto.simFilterSameWidth, disabled=db.dto.simModeCondGrp),
                    dbc.Checkbox(id=k.id(k.filterSameHeight), label="Same Height", value=db.dto.simFilterSameHeight, disabled=db.dto.simModeCondGrp),
                    dbc.Checkbox(id=k.id(k.filterSameSize), label="Same File Size", value=db.dto.simFilterSameSize, disabled=db.dto.simModeCondGrp),
                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Condition Group Search: "), "Search for multiple groups of similar photos that meet specific metadata conditions"]),
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
        out(k.id(k.filterSameDate), "disabled"),
        out(k.id(k.filterSameWidth), "disabled"),
        out(k.id(k.filterSameHeight), "disabled"),
        out(k.id(k.filterSameSize), "disabled"),
        out(k.id(k.filterMaxGroups), "disabled"),
    ],
    inp(k.id(k.ths), "value"),
    inp(k.id(k.autoNxt), "value"),
    inp(k.id(k.shGdInfo), "value"),
    inp(k.id(k.simIncRelGrp), "value"),
    inp(k.id(k.simMaxDepths), "value"),
    inp(k.id(k.simMaxItems), "value"),
    inp(k.id(k.filterEnable), "value"),
    inp(k.id(k.filterSameDate), "value"),
    inp(k.id(k.filterSameWidth), "value"),
    inp(k.id(k.filterSameHeight), "value"),
    inp(k.id(k.filterSameSize), "value"),
    inp(k.id(k.filterMaxGroups), "value"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def settings_ChgThs(ths, auNxt, shGdInfo, incRelGrp, maxDepths, maxItems, filterEnable, filterDate, filterWidth, filterHeight, filterSize, maxGroups, dta_now):
    retNow = noUpd

    now = models.Now.fromDict(dta_now)
    mi, mx = ths

    db.dto.simMin = co.vad.float(mi, 0.93, 0.50, 0.99)
    db.dto.simMax = co.vad.float(mx, 1.00, 0.51, 1.00)

    db.dto.autoNext = auNxt
    db.dto.simMaxDepths = maxDepths
    db.dto.simMaxItems = maxItems

    db.dto.simModeCondGrp = filterEnable
    db.dto.simFilterSameDate = filterDate
    db.dto.simFilterSameWidth = filterWidth
    db.dto.simFilterSameHeight = filterHeight
    db.dto.simFilterSameSize = filterSize
    db.dto.simFilterMaxGroups = maxGroups

    # Control filter enable/disable states
    filtersDisabled = not filterEnable
    maxGroupsDisabled = not filterEnable

    def reloadAssets():
        nonlocal retNow, now
        lg.info(f"[cSets] reload, incGroup[{db.dto.simIncRelGrp}]")
        now.sim.assCur = db.pics.getSimAssets(now.sim.assAid, db.dto.simIncRelGrp)
        retNow = now

    #now.sim.assCur = db.pics.getSimAssets(assId, db.dto.simIncRelGrp)

    if db.dto.showGridInfo != shGdInfo:
        db.dto.showGridInfo = shGdInfo
        if retNow == noUpd: reloadAssets()

    if db.dto.simIncRelGrp != incRelGrp:
        db.dto.simIncRelGrp = incRelGrp
        if retNow == noUpd: reloadAssets()

    # lg.info(f"[settings] changed: {ths}, {auNxt}, {shGdInfo}")

    return [retNow, filtersDisabled, filtersDisabled, filtersDisabled, filtersDisabled, maxGroupsDisabled]
