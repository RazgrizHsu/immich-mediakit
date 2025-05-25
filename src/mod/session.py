from typing import Any
from db import pics, psql, vecs
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

    if not now.usrs:
        uss = []
        try:
            rows = psql.fetchUsers()
            for r in rows:
                usr = models.Usr(r.get('id'), r.get('name'), r.get('email'), r.get('ak'))
                uss.append(usr)
        except:
            pass

        lg.info(f"[session] load usrs: {len(uss)}")
        now.usrs = uss

    usrId = dto.usrId
    if usrId:
        now.switchUsr(usrId)
        # lg.info( f"[session] set usrId[{usrId}] now.usr: {now.usr}" )

    now.useType = dto.useType
    if not now.photoQ:
        now.photoQ = dto.photoQ = ks.db.thumbnail

    now.cntPic = pics.count()
    now.cntVec = vecs.count()

    if not now.useType:
        now.useType = dto.useType = 'API'

    mk(ks.sto.now, now.toDict())

    mk(ks.sto.nfy, nfy.toDict())
    mk(ks.sto.tsk, tsk.toDict())
    mk(ks.sto.mdl, mdl.toDict())

    items.append(htm.Div(id=ks.sto.init, children='init'))

    return htm.Div(items, style={'display': 'none'})
