import dash.html as htm
import dash_bootstrap_components as dbc
from util import log
from conf import ks

lg = log.get(__name__)

def createExifTooltip(asset_id, exif_data):
    if not exif_data:
        return None

    exif_table = []

    for key in ks.defs.exif.keys():
        if key in exif_data and exif_data[key] is not None:
            display_key = ks.defs.exif.get(key, key)

            value = exif_data[key]
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
                display_value = str(value)

            exif_table.append(
                htm.Tr([
                    htm.Td(display_key, style={"fontWeight": "bold", "padding": "2px 8px"}),
                    htm.Td(display_value, style={"padding": "2px 8px"})
                ])
            )

    for key, value in exif_data.items():
        if key not in ks.defs.exif and value is not None:
            exif_table.append(
                htm.Tr([
                    htm.Td(key, style={"fontWeight": "bold", "padding": "2px 8px"}),
                    htm.Td(str(value), style={"padding": "2px 8px"})
                ])
            )

    if len(exif_table) > 0:
        return dbc.Tooltip(
            htm.Div([
                htm.H6("EXIF Information", className="mb-2"),
                htm.Table(
                    htm.Tbody(exif_table),
                    className="table-sm table-striped",
                    style={
                        "backgroundColor": "white",
                        "color": "black",
                        "width": "100%",
                        "borderRadius": "4px"
                    }
                )
            ], style={"maxWidth": "400px", "maxHeight": "400px", "overflow": "auto"}),
            target={"type": "exif-badge", "index": asset_id},
            placement="auto",
            style={"backgroundColor": "rgba(0,0,0,0.9)", "color": "white", "maxWidth": "450px"},
            className="tooltip-exif-info",
            delay={"show": 300, "hide": 100}
        )

    return None
