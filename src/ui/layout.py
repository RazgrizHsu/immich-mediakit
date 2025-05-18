from conf import envs, Ks
from dsh import htm, dbc, inp, out, ste
from util import log, models

lg = log.get(__name__)

#========================================================================
class K:
    class div:
        sideState = 'div-side-state'
        connInfo = 'div-conn-info'

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
            htm.Span(["🔄 Vectors"]),
            href=f"/{Ks.pgs.photoVec}",
            active="exact",
            id=K.nav.photoVec,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["🔍 Similar"]),
            href=f"/{Ks.pgs.findDups}",
            active="exact",
            id=K.nav.searchDups,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["🖼️ AssetsGrid"]),
            href=f"/{Ks.pgs.viewGrid}",
            active="exact",
            id=K.nav.viewGrid,
            className="custom-nav-link"
        )),
        dbc.NavItem(dbc.NavLink(
            htm.Span(["⚙️ Settings"]),
            href=f"/{Ks.pgs.settings}",
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
                        dbc.Col(dbc.NavbarBrand(f"{Ks.title}", className="ms-2")),
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
                        f"{Ks.title} © 2025 ",
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
def renderSideBar():
    return htm.Div(
        [
            htm.H5(f"{Ks.title}", className="text-center mb-4"),

            htm.Hr(),

            htm.Div([
                htm.Div(htm.Small("Cache Count:"), className="mb-2 text-muted"),
                htm.Div(id=K.div.sideState)
            ],
                className="mb-4"
            ),

            # htm.Hr(),
            # dbc.Row([
            # 	dbc.Col([htm.Div(id="div-test")], width=6),
            # 	dbc.Col([dbc.Button("test", id="btn-test", className="w-100")], width=6),
            # ], className="mb-4"),


            htm.Hr(),

            htm.Div(
                [
                    htm.Div(htm.Small("Connection Information"), className="mb-2 text-muted"),
                    htm.Div([htm.Div("---")], id=K.div.connInfo)
                ],
                className="mb-4"
            ),
        ],
        className="bg-dark p-3 h-100 border rounded"
    )

#========================================================================
def regBy(app):
    #------------------------------------------------------------------------
    @app.callback(
        out(K.nav.photoVec, 'disabled'),
        out(K.nav.searchDups, 'disabled'),
        out(K.nav.viewGrid, 'disabled'),
        inp(Ks.store.now, 'data')
    )
    def onNowChange(dta_now):
        if not dta_now: return True, True, True

        # lg.info("Registered pages:")
        # for page, config in dash.page_registry.items(): lg.info(f"- {page}: {config['path']}")

        now = models.Now.fromStore(dta_now)

        disPhotoVec = disViewGrid = now.cntPic <= 0
        disSearchDups = now.cntVec <= 0

        return disPhotoVec, disSearchDups, disViewGrid

    #------------------------------------------------------------------------
    @app.callback(
        out(K.div.sideState, "children"),
        [
            inp(Ks.store.now, "data")
        ]
    )
    def update_side_state(dta_now):
        now = models.Now.fromStore(dta_now)

        return htm.Div([

            dbc.Row([
                dbc.Col(htm.Small("Photo Count", className="d-inline-block me-2"), width=5),
                dbc.Col(dbc.Alert(f"{now.cntPic}", color="info", className="py-0 px-2 mb-2")),
            ]),
            dbc.Row([
                dbc.Col(htm.Small("Vector Count", className="d-inline-block me-2"), width=5),
                dbc.Col(dbc.Alert(f"{now.cntVec}", color="info", className="py-0 px-2 mb-2")),
            ]),
        ])


    #------------------------------------------------------------------------
    @app.callback(
        out(K.div.connInfo, "children"),
        inp(Ks.store.init, "children"),
        ste(Ks.store.now, "data")
    )
    def cb_init(_trigger, dta_now):
        lg.info("[layout] Initializing SideBar...")

        now = models.Now.fromStore(dta_now)

        info = [
            htm.P(["Data Source: ", htm.Strong(now.useType)], className="mb-2"),
            htm.P(["Server: ", htm.Code(envs.psqlHost or "Not set")], className="mb-2"),
            htm.P(["Database: ", htm.Code(envs.psqlDb or "Not set")], className="mb-2"),
            htm.P(["User: ", htm.Code(envs.psqlUser or "Not set")], className="mb-2"),
            htm.P(
                ["Password: ", htm.Code("--OK--" if envs.psqlPass else "--None--")],
                className="mb-2"
            )
        ]

        return info


#------------------------------------------------------------------------
# @app.callback(
# 	out("div-test", "children"),
# 	inp("btn-test", "n_clicks"),
# 	[ste(Ks.store.now, "data"), ste(Ks.store.assets, "data")],
# 	prevent_initial_call=True
# )
# def on_btn_test(n_clicks, dta_now, dta_assets):
# 	if not n_clicks: return dash.no_update
#
# 	# lg.info( f"[layout] Button clicked: {n_clicks}, dta_now[{dta_now}], dta_assets[{dta_assets}]" )
#
# 	return f"Button clicked {n_clicks} times"
