from dsh import dbc, inp, out, getTriggerId
from util import log, models
from conf import Ks

lg = log.get(__name__)

class k:

    class id:
        div = 'modal-container'
        btnOk = 'modal-btn-ok'
        btnNo = 'modal-btn-no'
        txt = 'modal-txt'

def render():
    return dbc.Modal([
        dbc.ModalHeader("Operation Confirm"),
        dbc.ModalBody("Are you sure you want to delete all acquired asset data? This will clear the local database.", id=k.id.txt),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=k.id.btnNo, className="ms-auto"),
            dbc.Button("Confirm", id=k.id.btnOk, color="danger"),
        ]),
    ], id=k.id.div, is_open=False),


#========================================================================
def regBy(app):
    #------------------------------------------------------------------------
    @app.callback(
        [
            out(Ks.store.mdl, "data", allow_duplicate=True),
            out(k.id.div, "is_open"),
            out(k.id.txt, "children"),
        ],
        [
            inp(Ks.store.mdl, "data"),
            inp(k.id.btnOk, "n_clicks"),
            inp(k.id.btnNo, "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def update_txt(dta_mdl, nclk_ok, nclk_no):
        mdl = models.Mdl.fromStore(dta_mdl)

        isOpen = mdl.id is not None

        trigId = getTriggerId()

        # lg.info( f"[modal] Trigger: {trigId} mdl: id[{mdl.id}] msg[{mdl.msg}]" )

        if trigId == k.id.btnNo:
            lg.info(f"[modal] Cancel execution: id[{mdl.id}]")
            mdl.reset()
            isOpen = False

        if trigId == k.id.btnOk:
            # lg.info( f"[modal] Confirm execution: id[{mdl.id}] {mdl.msg}" )
            mdl.ok = True
            isOpen = False

        return mdl.toStore(), isOpen, mdl.msg
