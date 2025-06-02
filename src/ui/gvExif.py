import dash.html as htm
import dash_bootstrap_components as dbc
from util import log
from conf import ks, co

lg = log.get(__name__)

from mod import models



def mkExifRows( asset:models.Asset ):

    rows = []

    if asset.jsonExif:
        rows = mkExifGrid( asset.jsonExif.toDict() )
        pass

    return rows

def mkExifGrid( dicExif:dict ):
    table = []

    for key in ks.defs.exif.keys():
        if key in dicExif and dicExif[key] is not None:
            display_key = ks.defs.exif.get(key, key)

            value = dicExif[key]
            if key == "fileSizeInByte" and isinstance(value, (int, float)):
                if value > 1024 * 1024:
                    display_value = f"{value / (1024 * 1024):.2f} MB"
                elif value > 1024:
                    display_value = f"{value / 1024:.2f} KB"
                else:
                    display_value = f"{value} B"
            elif key == "focalLength" and isinstance(value, (int, float)):
                display_value = f"{value} mm"
            elif key == "fNumber" and isinstance(value, (int, float)):
                display_value = f"f/{value}"
            else:
                if not value: continue
                display_value = co.fmt.date(value)

            table.append(
                htm.Tr([
                    htm.Td(display_key),
                    htm.Td(display_value),
                ])
            )

    # for key, value in dicExif.items():
    #     if key not in ks.defs.exif and value is not None:
    #         table.append(
    #             htm.Tr([
    #                 htm.Td(key),
    #                 htm.Td(str(value)),
    #             ])
    #         )

    return table


def mkTipExif(assId, dicExif: dict):
    if not dicExif: return None

    table = mkExifGrid(dicExif)

    if len(table) > 0:
        return dbc.Tooltip(
            htm.Div([
                htm.H6("EXIF Information", className="mb-2"),
                htm.Table(
                    htm.Tbody(table),
                    className="table-sm table-striped",
                    style={
                        "backgroundColor": "white",
                        "color": "black",
                        "width": "100%",
                        "borderRadius": "4px"
                    }
                )
            ], style={"maxWidth": "400px", "maxHeight": "400px", "overflow": "auto"}),
            target={"type": "exif-badge", "index": assId},
            placement="auto",
            style={"backgroundColor": "rgba(0,0,0,0.9)", "color": "white", "maxWidth": "450px"},
            className="tooltip-exif-info",
            delay={"show": 300, "hide": 100}
        )

    return None
