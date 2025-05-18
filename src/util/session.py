from typing import Any
from db import pics, psql, vecs
from db.dyn import dto
from dsh import htm, dcc
from util import log, models
from conf import Ks

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
    lg.info("[session] Initializing session data")

    now: models.Now = models.Now()
    nfy: models.Nfy = models.Nfy()
    tsk: models.Tsk = models.Tsk()
    mdl: models.Mdl = models.Mdl()

    if not now.usrs:
        uss = []
        try:
            rows = psql.fetchUsers()
            lg.info(f"[session] Loading users.. {len(rows)}")
            for r in rows:
                usr = models.Usr(r.get('id'), r.get('name'), r.get('email'), r.get('apiKey'))
                uss.append(usr)
        except:
            pass

        lg.info(f"[session] Initialized usrs: {len(uss)}")
        now.usrs = uss

    usrId = dto.usrId
    if usrId: now.switchUsr(usrId)

    now.useType = dto.useType

    now.cntPic = pics.count()
    now.cntVec = vecs.count()

    if not now.useType:
        now.useType = dto.useType = 'API'

    mk(Ks.store.now, now.toStore())

    mk(Ks.store.nfy, nfy.toStore())
    mk(Ks.store.tsk, tsk.toStore())
    mk(Ks.store.mdl, mdl.toStore())

    items.append(htm.Div(id=Ks.store.init, children='init'))

    return htm.Div(items, style={'display': 'none'})
