from conf import ks
from dsh import htm, dbc, inp, out, ste, callback
from util import log, models

lg = log.get(__name__)

#========================================================================
class k:
    class nav:
        assets = 'nav-assets'
        photoVec = 'nav-photoVec'
        searchDups = 'nav-searchDups'
        viewGrid = 'nav-viewGrid'
        settings = 'nav-settings'


#========================================================================
def renderHeader():
    items = [
        dbc.NavItem(dbc.NavLink(
            htm.Span(["⚡️ Fetch"]),
            href="/",
            active="exact",
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["🖼️ Assets"]),
            href=f"/{ks.pg.viewGrid}",
            active="exact",
            id=k.nav.viewGrid,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["🔄 Vectors"]),
            href=f"/{ks.pg.vector}",
            active="exact",
            id=k.nav.photoVec,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["🔍 Similar"]),
            href=f"/{ks.pg.similar}",
            active="exact",
            id=k.nav.searchDups,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["⚙️ Settings"]),
            href=f"/{ks.pg.settings}",
            active="exact",
            className="custom-nav-link"
        )),
    ]

    return dbc.Navbar(
        dbc.Container([
            htm.A(
                dbc.Row(
                    [
                        dbc.Col(htm.Img(src="assets/logo.png", height="38px"), width="auto", className="px-2"),
                        dbc.Col(dbc.NavbarBrand(f"{ks.title}", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),

            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

            dbc.Collapse(
                dbc.Nav(items, className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
            fluid=True
        ),
        color="dark",
        dark=True,
        className="px-2 nav-glow",
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
from . import sidebar
def renderBody(top, bottom):
    from util import task

    return htm.Div([

        #sidebar.layout(),

        htm.Div(
            [
                task.render(),
                *top,
            ],
            className="main"
        ),

        *bottom

    ], className="body")


#========================================================================
#------------------------------------------------------------------------
@callback(
    out(k.nav.photoVec, 'disabled'),
    out(k.nav.searchDups, 'disabled'),
    out(k.nav.viewGrid, 'disabled'),
    inp(ks.sto.now, 'data')
)
def onUpdateMenus(dta_now):
    if not dta_now: return True, True, True

    # lg.info("Registered pages:")
    # for page, config in dash.page_registry.items(): lg.info(f"- {page}: {config['path']}")

    now = models.Now.fromStore(dta_now)

    disVec = now.cntPic <= 0
    disGrd = disVec
    disDup = now.cntVec <= 0

    return disVec, disDup, disGrd

#------------------------------------------------------------------------
