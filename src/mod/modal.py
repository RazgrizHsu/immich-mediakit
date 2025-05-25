from dsh import dbc, inp, out, callback, getTriggerId
from util import log
from mod import models
from conf import ks

lg = log.get(__name__)

class k:

    class id:
        div = 'modal-container'
        btnOk = 'modal-btn-ok'
        btnNo = 'modal-btn-no'
        txt = 'modal-txt'

def render():
    return dbc.Modal([
        dbc.ModalHeader("Confirm"),
        dbc.ModalBody("", id=k.id.txt),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=k.id.btnNo, className="ms-auto"),
            dbc.Button("Confirm", id=k.id.btnOk, color="danger"),
        ]),
    ], id=k.id.div, is_open=False, centered=True),


#========================================================================
@callback(
    [
        out(k.id.div, "is_open"),
        out(k.id.txt, "children"),
        out(ks.sto.mdl, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    [
        inp(ks.sto.mdl, "data"),
        inp(k.id.btnOk, "n_clicks"),
        inp(k.id.btnNo, "n_clicks"),
    ],
    prevent_initial_call=True
)
def update_txt(dta_mdl, nclk_ok, nclk_no):
    mdl = models.Mdl.fromDict(dta_mdl)
    tsk = models.Tsk()

    isOpen = mdl.id is not None

    trigId = getTriggerId()

    # lg.info( f"[modal] Trigger[{trigId}] mdl: id[{mdl.id}]" )

    if trigId == k.id.btnNo:
        lg.info(f"[modal] Cancel execution: id[{mdl.id}]")
        mdl.reset()
        isOpen = False

    if trigId == k.id.btnOk:
        lg.info( f"[modal] Confirm execution: id[{mdl.id}] cmd[{mdl.cmd}]" )
        mdl.ok = True
        isOpen = False

        if mdl.cmd:
            tsk = mdl.mkTsk()
            if not tsk:
                lg.error(f"[modal] Failed to create task from modal")
                tsk = models.Tsk()
            else:
                lg.info(f"[modal] Created task: id[{tsk.id}] cmd[{tsk.cmd}]")

        mdl.reset()

    return isOpen, mdl.msg, mdl.toDict(), tsk.toDict()
