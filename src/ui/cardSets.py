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


def renderCard():


    lg.info( f"===============>> { db.dto.simMaxDepths } ({type(db.dto.simMaxDepths)})" )

    return dbc.Card([
        dbc.CardHeader("Similar Settings"),
        dbc.CardBody([
            htm.Div([
                htm.Label("Threshold Range", className="txt-sm"),
                htm.Div([
                    dcc.RangeSlider(
                        id=k.id(k.ths), min=0.5, max=1, step=0.01, marks=ks.defs.thMarks,
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

                    htm.Div( [
                        htm.Label( "Max Depths: " ),
                        dbc.Select(id=k.id(k.simMaxDepths), options=optMaxDepths, value=db.dto.simMaxDepths, className="")
                    ]),

                    htm.Div( [
                        htm.Label( "Max Items: " ),
                        dbc.Select(id=k.id(k.simMaxItems), options=optMaxItems, value=db.dto.simMaxItems, className="")
                    ]),
                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Include Related: "), "Display all images in the similarity group (not just direct matches). All displayed images will be affected by Keep/Delete operations"]),
                    htm.Li([htm.B("Max Depths: "), "During Find Similar, how many levels of hierarchical relationships to include in the same group (0 = direct matches only)"]),
                    htm.Li([htm.B("Max Items: "), "Maximum number of images to process during similarity search to prevent UI slowdown"])
                ])
            ], className="irow"),
        ])
    ], className="mb-0")


@cbk(
    [
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp(k.id(k.ths), "value"),
    inp(k.id(k.autoNxt), "value"),
    inp(k.id(k.shGdInfo), "value"),
    inp(k.id(k.simIncRelGrp), "value"),
    inp(k.id(k.simMaxDepths), "value"),
    inp(k.id(k.simMaxItems), "value"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def settings_ChgThs(ths, auNxt, shGdInfo, incRelGrp, maxDepths, maxItems, dta_now):
    retNow = noUpd

    now = models.Now.fromDict(dta_now)
    mi, mx = ths

    db.dto.simMin = co.vad.float(mi, 0.93, 0.50, 0.99)
    db.dto.simMax = co.vad.float(mx, 1.00, 0.51, 1.00)

    db.dto.autoNext = auNxt
    db.dto.simMaxDepths = maxDepths
    db.dto.simMaxItems = maxItems

    def reloadAssets():
        nonlocal retNow, now
        lg.info( f"[cSets] reload, incGroup[{db.dto.simIncRelGrp}]" )
        now.sim.assCur = db.pics.getSimAssets(now.sim.assAid, db.dto.simIncRelGrp)
        retNow = now

    #now.sim.assCur = db.pics.getSimAssets(assId, db.dto.simIncRelGrp)

    if db.dto.showGridInfo != shGdInfo:
        db.dto.showGridInfo = shGdInfo
        if retNow == noUpd: reloadAssets()

    if db.dto.simIncRelGrp != incRelGrp:
        db.dto.simIncRelGrp = incRelGrp
        if retNow == noUpd: reloadAssets()

    lg.info(f"[settings] changed: {ths}, {auNxt}, {shGdInfo}")

    return [retNow]
