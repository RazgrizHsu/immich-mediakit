from typing import Any
from dsh import htm, dcc

from db import dto
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
    if not photoQ or photoQ not in [ ks.db.thumbnail, ks.db.preview, ks.db.fullsize ]:
        photoQ = dto.photoQ = ks.db.thumbnail

    now.photoQ = photoQ


    from conf import co
    dto.simMin = co.valid.float( dto.simMin, 0.93 )
    dto.simMax = co.valid.float( dto.simMax, 1.00 )



    cnt = models.Cnt()
    cnt.refreshFromDB()


    mk(ks.sto.now, now.toDict())
    mk(ks.sto.nfy, nfy.toDict())
    mk(ks.sto.tsk, tsk.toDict())
    mk(ks.sto.mdl, mdl.toDict())
    mk(ks.sto.cnt, cnt.toDict())


    items.append(htm.Div(id=ks.sto.init, children='init'))

    return htm.Div(items, style={'display': 'none'})
