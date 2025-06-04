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

    @staticmethod
    def id(name):
        return {"type": "sets", "id": f"{name}"}


optMaxDepths = [
    {"label": "0", "value":0 },
    {"label": "1", "value":1 },
    {"label": "2", "value":2 },
    {"label": "3", "value":3 },
]


def renderCard():
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
                ], className="icbxs"),
                htm.Ul([
                    htm.Li([htm.B("Inlcude Related: "), "在current中將顯示關聯群組, 請注意, 這些圖片將一起受到您的keep/delete命令影響"]),
                    htm.Li([htm.B("Max Depths: "), "當進行Find Similar的時候，會將多少階層的關聯圖片標記為同一個群組"])
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
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def settings_ChgThs(ths, auNxt, shGdInfo, incRelGrp, maxDepths, dta_now):
    retNow = noUpd

    lg.info( f"maxDepths: {maxDepths}" )

    now = models.Now.fromDict(dta_now)
    mi, mx = ths

    db.dto.simMin = co.vad.float(mi, 0.93, 0.50, 0.99)
    db.dto.simMax = co.vad.float(mx, 1.00, 0.51, 1.00)

    db.dto.autoNext = auNxt

    if db.dto.showGridInfo != shGdInfo:
        db.dto.showGridInfo = shGdInfo
        if retNow == noUpd: retNow = now.toDict()

    if db.dto.simIncRelGrp != incRelGrp:
        db.dto.simIncRelGrp = incRelGrp
        if retNow == noUpd: retNow = now.toDict()

    lg.info(f"[settings] changed: {ths}, {auNxt}, {shGdInfo}")

    return [retNow]
