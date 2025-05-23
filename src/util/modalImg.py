from dsh import dash, htm, dcc, dbc, inp, out, ste, callback, noUpd, getTriggerId
from util import log
from conf import ks

lg = log.get(__name__)



class k:
	class img:
		modal = "img-modal"
		modalImg = "img-modal-content"
		modalStore = ks.sto.mdlImg
		btnModeChg = "btn-img-mode-chg"

	txtHAuto = "🔄 Auto Height"
	txtHFix = "🔄 Fixed Height"
	clsAuto = "auto"

def render():
	return [
		dbc.Modal([
			dbc.ModalHeader([
				htm.Span("Image Preview", className="me-auto"),
				dbc.Button(
					k.txtHFix,
					id=k.img.btnModeChg,
					color="secondary",
					size="sm",
					className="me-2",
					style={"fontSize": "0.85rem"}
				),
			], close_button=True),
			dbc.ModalBody(
				htm.Img(id=k.img.modalImg)
			),
		],
			id=k.img.modal,
			size="xl",
			centered=True,
			fullscreen=True,
			className="img-pop",
		),

		# Store for clicked image ID
		dcc.Store(id=k.img.modalStore, data=None)
	]

#------------------------------------------------------------------------
# Image Preview Modal Callback
#------------------------------------------------------------------------
@callback(
	out(k.img.modal, "is_open"),
	[
		inp(k.img.modalStore, "data"),
	],
	ste(k.img.modal, "is_open"),
	prevent_initial_call=True
)
def toggle_modal_visibility(store_data, is_open):
	ctx = dash.callback_context
	if not ctx.triggered: return noUpd

	trigger_id = getTriggerId()

	if trigger_id == k.img.modalStore:
		if store_data:
			return True
		else:
			return False

	return noUpd


@callback(
	out(k.img.modalStore, "data"),
	inp({"type": "img-pop", "index": dash.ALL}, "n_clicks"),
	prevent_initial_call=True
)
def store_clicked_image(all_clicks):
	if not all_clicks or not any(clicks > 0 for clicks in all_clicks): return noUpd

	ctx = dash.callback_context
	if not ctx.triggered: return noUpd

	trigger_idx = ctx.triggered_id
	if isinstance(trigger_idx, dict) and "index" in trigger_idx:
		asset_id = trigger_idx["index"]
		lg.info(f"Image clicked, asset_id[{asset_id}] clicked[{all_clicks}]")

		if asset_id and str(asset_id).startswith("noimg"):
			return "assets/noimg.png"
		else:
			return f"/api/img/{asset_id}?q=preview"

	return noUpd

@callback(
	out(k.img.modalImg, "src"),
	inp(k.img.modalStore, "data"),
	prevent_initial_call=True
)
def update_modal_content(img_src):
	if img_src:
		lg.info(f"Setting modal src to: {img_src}")
		return img_src
	return noUpd


@callback(
	[
		out(k.img.modal, "className"),
		out(k.img.btnModeChg, "children")
	],
	[inp(k.img.btnModeChg, "n_clicks")],
	[ste(k.img.modal, "className")],
	prevent_initial_call=True
)
def toggle_img_class_and_update_text(n_clicks, classes):
	if not n_clicks: return [noUpd, noUpd]

	if not classes: classes = ""

	hasClass = k.clsAuto in classes.split()

	if hasClass:
		new_classes = " ".join([c for c in classes.split() if c != k.clsAuto])
		button_text = k.txtHFix
	else:
		new_classes = classes + f" {k.clsAuto}" if classes else k.clsAuto
		button_text = k.txtHAuto

	return [new_classes, button_text]
