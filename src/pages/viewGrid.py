import db
from conf import ks
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId
from mod import models
from ui.grid import createGrid
from util import log

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.viewGrid}',
    title=f"{ks.title}: " + 'Assets Grid',
)

class K:
    class inp:
        selectUsrId = "inp-grid-user-selector"
        selectSortBy = "inp-grid-sort-by"
        selectSortOrder = "inp-grid-sort-order"
        selectFilter = "inp-grid-filter"
        searchKeyword = "inp-grid-search"
        checkFavorites = "inp-grid-favorites-only"
        selectPerPage = "inp-grid-per-page"

    class div:
        grid = "div-photo-grid"
        pagination = "div-grid-pagination"
        pgIdx = "vg-pg-idx"
        loadingIndicator = "div-grid-loading"
        btnNextPage = "btn-grid-next-page"
        btnPrevPage = "btn-grid-prev-page"
        dataPaged = "store-grid-pagination"


#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================
        dbc.Row([
            dbc.Col(htm.H3(f"{ks.pg.viewGrid.name}"), width=3),
            dbc.Col(htm.Small(f"{ks.pg.viewGrid.desc}", className="text-muted"))
        ], className="mb-4"),

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
                        dbc.Label("Sort By"),
                        dcc.Dropdown(
                            id=K.inp.selectSortBy,
                            options=[
                                {"label": "Date Created", "value": "fileCreatedAt"},
                                {"label": "Date Modified", "value": "fileModifiedAt"},
                                {"label": "File Name", "value": "originalFileName"}
                            ],
                            value="fileCreatedAt",
                            clearable=False,
                            className="mb-2"
                        ),
                    ], width=4),

                    dbc.Col([
                        dbc.Label("Order"),
                        dcc.Dropdown(
                            id=K.inp.selectSortOrder,
                            options=[
                                {"label": "Ascending", "value": "asc"},
                                {"label": "Descending", "value": "desc"}
                            ],
                            value="desc",
                            clearable=False,
                            className="mb-2"
                        ),
                    ], width=4),
                ]),

                dbc.Row([
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

        dbc.Spinner(
            htm.Div(id=K.div.grid, className="mb-4"),
            color="primary",
            type="border",
            spinner_style={"width": "3rem", "height": "3rem"}
        ),

        # Pagination
        dbc.Row([
            dbc.Col([
                dbc.Button("Previous", id=K.div.btnPrevPage, color="primary", disabled=True, className="w-100")
            ], width=4),

            dbc.Col([
                htm.Div([
                    htm.Span("Page: "),
                    dbc.Input(id=K.div.pgIdx, type="number", min=1, value=1, style={"width": "80px", "display": "inline-block"}, className="mx-2"),
                    htm.Span("of "),
                    htm.Span(id=K.div.pagination, className="ms-2")
                ], className="text-center")
            ], width=4),

            dbc.Col([
                dbc.Button(
                    "Next",
                    id=K.div.btnNextPage,
                    color="primary",
                    className="w-100"
                )
            ], width=4),
        ], className="mt-3 mb-4"),

        dcc.Store(id=K.div.dataPaged, data={"page": 1, "per_page": 24, "total": 0}),

        #====== bottom end ======================================================
    ])

#========================================================================
# Page initialization
#========================================================================
@callback(
    [
        out(K.inp.selectUsrId, "options"),
        out(K.div.dataPaged, "data"),
    ],
    inp(ks.sto.cnt, "data"),
    inp(ks.sto.now, "data"),
    prevent_initial_call=False
)
def viewGrid_Init(dta_cnt, dta_now):
    cnt = models.Cnt.fromDict(dta_cnt)
    now = models.Now.fromDict(dta_now)

    opts = [{"label": "All Users", "value": ""}]
    if now.usrs and len(now.usrs) > 0:
        for usr in now.usrs: opts.append({"label": usr.name, "value": usr.id})

    data = {"page": 1, "per_page": 24, "total": cnt.ass or 0}

    return opts, data


#========================================================================
# Handle filter changes and pagination controls
#========================================================================
@callback(
    out(K.div.dataPaged, "data", allow_duplicate=True),
    [
        inp(K.inp.selectUsrId, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.checkFavorites, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.selectPerPage, "value"),
        inp(K.div.btnNextPage, "n_clicks"),
        inp(K.div.btnPrevPage, "n_clicks"),
        inp(K.div.pgIdx, "value"),
    ],
    [
        ste(K.div.dataPaged, "data"),
        ste(K.inp.selectUsrId, "value"),
        ste(K.inp.selectFilter, "value"),
        ste(K.inp.checkFavorites, "value"),
        ste(K.inp.searchKeyword, "value"),
    ],
    prevent_initial_call=True
)
def on_pagination_controls(
    usrId, filterOption, favoritesOnly, schKey, pgSize,
    clks_next, clks_prev, currentPage,
    dta_pgd, stateUsrId, stateFilterOption, stateFavoritesOnly, stateSearchKeyword
):
    trigger = getTriggerId()

    filter_triggers = [
        K.inp.selectUsrId, K.inp.selectFilter,
        K.inp.checkFavorites, K.inp.searchKeyword,
        K.inp.selectPerPage
    ]

    if trigger in filter_triggers:
        dta_pgd["page"] = 1
        dta_pgd["per_page"] = pgSize

        total = db.pics.countFiltered(
            usrId=usrId,
            opts=filterOption,
            search=schKey,
            favOnly=favoritesOnly
        )
        dta_pgd["total"] = total

        return dta_pgd

    page = dta_pgd["page"]
    per_page = dta_pgd["per_page"]
    total = dta_pgd["total"]

    total_pages = max(1, (total + per_page - 1) // per_page)

    if trigger == K.div.btnNextPage and clks_next:
        page = min(page + 1, total_pages)
    elif trigger == K.div.btnPrevPage and clks_prev:
        page = max(1, page - 1)
    elif trigger == K.div.pgIdx:
        page = max(1, min(currentPage, total_pages)) if currentPage else 1

    dta_pgd["page"] = page

    return dta_pgd


#========================================================================
# Handle photo grid loading
#========================================================================
@callback(
    [
        out(K.div.grid, "children"),
        out(K.div.pagination, "children"),
        out(K.div.pgIdx, "value"),
        out(K.div.pgIdx, "max"),
        out(K.div.btnPrevPage, "disabled"),
        out(K.div.btnNextPage, "disabled"),
    ],
    [
        inp(K.div.dataPaged, "data"),
        inp(K.inp.selectUsrId, "value"),
        inp(K.inp.selectSortBy, "value"),
        inp(K.inp.selectSortOrder, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.checkFavorites, "value"),
    ],
    ste(ks.sto.now, "data"),
    ste(ks.sto.cnt, "data"),
    prevent_initial_call=False
)
def viewGrid_Load(dta_pg, usrId, sortBy, sortOrd, filOpt, shKey, onlyFav, dta_now, dta_cnt):
    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)

    page = dta_pg["page"]
    pageSize = dta_pg["per_page"]
    total = dta_pg["total"]

    if cnt.ass <= 0: return htm.Div("No photos available"), "0", 1, 1, True, True

    total_pages = max(1, (total + pageSize - 1) // pageSize)

    pageIdx = min(total_pages, max(1, page))

    photos = db.pics.getFiltered(usrId, sortBy, sortOrd, filOpt, shKey, onlyFav, pageIdx, pageSize)

    if photos and len(photos) > 0:
        lg.info(f"Loaded {len(photos)} photos")
    else:
        lg.info("No photos loaded")

    grid = createGrid(photos)

    prev_disabled = pageIdx <= 1
    next_disabled = pageIdx >= total_pages

    return grid, f"{total_pages}", pageIdx, total_pages, prev_disabled, next_disabled

