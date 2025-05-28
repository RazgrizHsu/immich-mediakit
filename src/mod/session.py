from typing import Any
from db.dyn import dto
from dsh import htm, dcc

from util import log
from mod import models
from conf import ks

lg = log.get(__name__)


def render():
    items: list[Any] = []

    def mk(kid, dta):
        sto = dcc.Store(
            id=kid,
            storage_type='session',  # memory, local, session
            data=dta
        )
        items.append(sto)

    lg.info("---------------------------------------")
    lg.info("[session] Initializing..")

    now: models.Now = models.Now()
    nfy: models.Nfy = models.Nfy()
    tsk: models.Tsk = models.Tsk()
    mdl: models.Mdl = models.Mdl()


    now.usrId = dto.usrId

    photoQ = dto.photoQ
    if not photoQ: photoQ = dto.photoQ = ks.db.thumbnail

    now.photoQ = photoQ



    cnt = models.Cnt()
    cnt.refreshFromDB()


    mk(ks.sto.now, now.toDict())
    mk(ks.sto.nfy, nfy.toDict())
    mk(ks.sto.tsk, tsk.toDict())
    mk(ks.sto.mdl, mdl.toDict())
    mk(ks.sto.cnt, cnt.toDict())


    items.append(htm.Div(id=ks.sto.init, children='init'))

    return htm.Div(items, style={'display': 'none'})
