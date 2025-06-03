import db
from conf import ks
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, noUpd
from mod import models
from mod.models import Pager
from ui.gv import createGrid
from ui import pager
from util import log

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.view}',
    title=f"{ks.title}: " + 'Assets Grid',
)

class K:
    class inp:
        selectUsrId = "inp-grid-user-selector"
        selectFilter = "inp-grid-filter"
        searchKeyword = "inp-grid-search"
        checkFavorites = "inp-grid-favorites-only"
        selectPerPage = "inp-grid-per-page"

    class div:
        grid = "div-photo-grid"
        pagerMain = "vg-pager-main"


#========================================================================
def layout():
    import ui

    # Get initial total for display
    try:
        total = db.pics.count()
    except:
        total = 0

    return ui.renderBody([
        #====== top start =======================================================

        htm.Div([
            htm.H3(f"{ks.pg.view.name}"),
            htm.Small(f"{ks.pg.view.desc}", className="text-muted")
        ], className="body-header"),

        dbc.Card([
            dbc.CardHeader("View Settings"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("User"),
                        dcc.Dropdown(
                            id=K.inp.selectUsrId,
                            options=[{"label": "All Users", "value": ""}],
                            value="",
                            clearable=False,
                            className="mb-2"
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Filter"),
                        dcc.Dropdown(
                            id=K.inp.selectFilter,
                            options=[
                                {"label": "All Assets", "value": "all"},
                                {"label": "With Vectors", "value": "with_vectors"},
                                {"label": "Without Vectors", "value": "without_vectors"}
                            ],
                            value="all",
                            clearable=False,
                            className="mb-2"
                        ),
                    ], width=4),
                ]),

                dbc.Row([


                    dbc.Col([
                        dbc.Label("Search"),
                        dbc.Input(
                            id=K.inp.searchKeyword,
                            type="text",
                            placeholder="Search by filename...",
                            className="mb-2"
                        ),
                    ], width=4),

                    dbc.Col([
                        dbc.Label(" "),
                        dbc.Checkbox(
                            id=K.inp.checkFavorites,
                            label="Favorites Only",
                            value=False,
                            className="mt-2"
                        ),
                    ], width=4),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Assets Per Page"),
                        dcc.Dropdown(
                            id=K.inp.selectPerPage,
                            options=[
                                {"label": "12", "value": 12},
                                {"label": "24", "value": 24},
                                {"label": "48", "value": 48},
                                {"label": "96", "value": 96}
                            ],
                            value=24,
                            clearable=False,
                            className="mb-2"
                        ),
                    ], width=12),
                ]),
            ])
        ], className="mb-4"),
        #====== top end =========================================================
    ], [
        #====== bottom start=====================================================

        htm.Div([
            # Top pager
            *pager.createPager(pgId=K.div.pagerMain, idx=0, className="mb-3 text-center", btnSize=7 ),

            # Grid
            dbc.Spinner(
                htm.Div(id=K.div.grid, className="mb-4"),
                color="primary",
                type="border",
                spinner_style={"width": "3rem", "height": "3rem"}
            ),

            # Bottom pager
            *pager.createPager(pgId=K.div.pagerMain, idx=1, className="mt-3 text-center", btnSize=7),

            # Main pager store
            *pager.createStore(pgId=K.div.pagerMain, page=1, size=24, total=total)
        ])

        #====== bottom end ======================================================
    ])

#========================================================================
# Register pager callbacks
#========================================================================
pager.regCallbacks(K.div.pagerMain)

#========================================================================
# Page initialization - initialize user options
#========================================================================
@callback(
    out(K.inp.selectUsrId, "options"),
    [
        inp(ks.sto.cnt, "data"),
        inp(ks.sto.now, "data"),
    ],
    prevent_initial_call=False
)
def vw_Init(dta_cnt, dta_now):
    cnt = models.Cnt.fromDict(dta_cnt)
    now = models.Now.fromDict(dta_now)

    opts = [{"label": "All Users", "value": ""}]
    usrs = db.psql.fetchUsers()
    if usrs and len(usrs) > 0:
        for usr in usrs:
            opts.append({"label": usr.name, "value": usr.id})

    return opts


#========================================================================
# Handle filter changes - reset to page 1
#========================================================================
@callback(
    out(pager.id.store(K.div.pagerMain), "data", allow_duplicate=True),
    [
        inp(K.inp.selectUsrId, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.checkFavorites, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.selectPerPage, "value"),
    ],
    ste(pager.id.store(K.div.pagerMain), "data"),
    prevent_initial_call=True
)
def vw_OnFilterChange(
    usrId, filterOption, favoritesOnly, schKey, pgSize,
    dta_pgr
):
    pgr = Pager.fromDict(dta_pgr)

    # Update total count based on filters
    total = db.pics.countFiltered(
        usrId=usrId,
        opts=filterOption,
        search=schKey,
        favOnly=favoritesOnly
    )

    # Reset to page 1 and update size
    pgr.idx = 1
    pgr.size = pgSize
    pgr.cnt = total

    lg.info(f"[vw] Filter changed, total: {total}, size: {pgSize}")

    return pgr.toDict()


#========================================================================
# Handle photo grid loading when pager changes
#========================================================================
@callback(
    out(K.div.grid, "children"),
    [
        inp(pager.id.store(K.div.pagerMain), "data"),
        inp(K.inp.selectUsrId, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.checkFavorites, "value"),
    ],
    ste(ks.sto.cnt, "data"),
    prevent_initial_call=True
)
def vw_Load(dta_pgr, usrId, filOpt, shKey, onlyFav, dta_cnt):
    if not dta_pgr: return noUpd

    cnt = models.Cnt.fromDict(dta_cnt)
    pgr = Pager.fromDict(dta_pgr)

    if cnt.ass <= 0:
        return dbc.Alert("No photos available", color="secondary", className="text-center")

    photos = db.pics.getFiltered(usrId, filOpt, shKey, onlyFav, pgr.idx, pgr.size)

    if photos and len(photos) > 0:
        lg.info(f"[vg:load] Loaded {len(photos)} photos for page {pgr.idx}")
    else:
        lg.info(f"[vg:load] No photos found for page {pgr.idx}")
        return dbc.Alert("No photos found matching your criteria", color="info", className="text-center")

    grid = createGrid(photos)

    return grid
