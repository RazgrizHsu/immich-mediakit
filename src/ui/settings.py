from dsh import htm, dcc, dbc, inp, out, ste, callback

from util import log

lg = log.get(__name__)

from conf import ks, co
import db


class k:
    ths = "thresholds"
    autoNxt = "autoNext"
    shGdInfo = "showGridInfo"

    @staticmethod
    def id(name):
        return {"type": "sets", "id": f"{name}"}


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
                ], className="mt-2 mb-1"),
                htm.Ul([
                    htm.Li("Thresholds set min/max similarity for image matching", className="text-muted")
                ])
            ], className="irow"),

            htm.Div([
                htm.Label("Find Settings", className="txt-sm"),
                htm.Div([
                    dbc.Checkbox(id=k.id(k.autoNxt), label="Auto Find Next", value=db.dto.autoNext),
                    dbc.Checkbox(id=k.id(k.shGdInfo), label="Show Grid Info", value=db.dto.showGridInfo),
                ], className="icbxs mt-2 mb-1"),
            ], className="irow"),
        ])
    ], className="mb-0")


@callback(
    [],
    inp(k.id(k.ths), "value"),
    inp(k.id(k.autoNxt), "value"),
    inp(k.id(k.shGdInfo), "value"),
)
def settings_ChgThs(ths, auNxt, shGdInfo):
    mi, mx = ths

    db.dto.simMin = co.vad.float(mi, 0.93, 0.50, 0.99)
    db.dto.simMax = co.vad.float(mx, 1.00, 0.51, 1.00)

    db.dto.autoNext = auNxt
    db.dto.showGridInfo = shGdInfo

    lg.info(f"[settings] changed: {ths}, {auNxt}, {shGdInfo}")
