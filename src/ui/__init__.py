from conf import ks
from dsh import htm, dbc, inp, out, cbk
from util import log
from mod import tsk, models

# public for refs
from . import sidebar
from . import pager

lg = log.get(__name__)

#========================================================================
class k:
    class nav:
        vec = 'nav-vector'
        sim = 'nav-similar'
        view = 'nav-view'


#========================================================================
def renderHeader():
    defs = [
        dbc.NavLink(htm.Span([f"⚙️ {ks.pg.setting.name}"]), href=f"/", active="exact", className="navLnk"),
        dbc.NavLink(htm.Span([f"⚡️ {ks.pg.fetch.name}"]), href=f"/{ks.pg.fetch}", active="exact", className="navLnk"),
        dbc.NavLink(htm.Span([f"🔄 {ks.pg.vector.name}"]), href=f"/{ks.pg.vector}", active="exact", id=k.nav.vec, className="navLnk"),
        dbc.NavLink(htm.Span([f"🔍 {ks.pg.similar.name}"]), href=f"/{ks.pg.similar}", active="exact", id=k.nav.sim, className="navLnk"),
        dbc.NavLink(htm.Span([f"🖼️ {ks.pg.view.name}"]), href=f"/{ks.pg.view}", active="exact", id=k.nav.view, className="navLnk"),
    ]

    return dbc.Navbar(
        dbc.Container([
            htm.A(
                dbc.Row([
                    dbc.Col(htm.Img(src="assets/logo.png", height="38px"), width="auto", className="px-1"),
                    dbc.Col(dbc.NavbarBrand(f"{ks.title}", className="ms-2")),
                ],
                    align="center", className="g-0",
                ),
                href="/", style={"textDecoration": "none"},
            ),

            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

            dbc.Collapse(
                dbc.Nav([dbc.NavItem(lnk) for lnk in defs], className="ms-auto", navbar=True),
                id="navbar-collapse", navbar=True,
            ),
        ],
            fluid=True
        ),
        color="dark", dark=True, className="px-1 nav-glow"
    )


#========================================================================
def renderFooter():
    return htm.Div(
        dbc.Container([
            dbc.Row([
                dbc.Col(
                    htm.Div([
                        f"{ks.title} © 2025 ",
                        htm.A(" GitHub ", href="https://github.com/RazgrizHsu/immich-mediakit", target="_blank")
                    ], className="text-center text-sm"),
                    width=12
                ),
            ]),
        ], fluid=True
        ),
        className="footer bg-dark"
    )


#========================================================================
def renderBody(top, bottom):
    return htm.Div([

        htm.Div(
            [
                *top,
            ],
            className="main"
        ),

        tsk.render(),

        *bottom

    ], className="body")


#========================================================================
#------------------------------------------------------------------------
@cbk(
    out(k.nav.vec, 'disabled'),
    out(k.nav.sim, 'disabled'),
    out(k.nav.view, 'disabled'),
    inp(ks.sto.cnt, 'data')
)
def onUpdateMenus(dta_cnt):
    if not dta_cnt: return True, True, True

    # lg.info("Registered pages:")
    # for page, config in dash.page_registry.items(): lg.info(f"- {page}: {config['path']}")

    cnt = models.Cnt.fromDic(dta_cnt)

    disVec = cnt.ass <= 0
    disSim = cnt.vec <= 0
    disView = disVec

    return disVec, disSim, disView

#------------------------------------------------------------------------
