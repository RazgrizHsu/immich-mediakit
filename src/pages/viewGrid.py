import db
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId
from util import log
from mod import models
from conf import ks
from ui.grid import createGrid

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{ks.pg.viewGrid}',
    title=f"{ks.title}: " + 'Assets Grid',
)

class K:
    class inp:
        selectUserId = "inp-grid-user-selector"
        selectSortBy = "inp-grid-sort-by"
        selectSortOrder = "inp-grid-sort-order"
        selectFilter = "inp-grid-filter"
        searchKeyword = "inp-grid-search"
        checkFavorites = "inp-grid-favorites-only"
        selectPerPage = "inp-grid-per-page"

    class div:
        grid = "div-photo-grid"
        pagination = "div-grid-pagination"
        currentPage = "inp-grid-current-page"
        noDataAlert = "div-no-data-alert"
        loadingIndicator = "div-grid-loading"
        btnNextPage = "btn-grid-next-page"
        btnPrevPage = "btn-grid-prev-page"
        paginationStore = "store-grid-pagination"


#========================================================================
def layout():
    import ui
    return ui.renderBody([
        #====== top start =======================================================

        htm.H3("Assets", className="mb-4"),
        htm.P([
            "View and organize your photos in a grid layout.", htm.Br(),
            "Use the filters and sorting options to customize your view."
        ],
            className="mb-4"
        ),

        dbc.Card([
            dbc.CardHeader("View Settings"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("User"),
                        dcc.Dropdown(
                            id=K.inp.selectUserId,
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

        htm.Div(
            dbc.Alert(
                "No photos available. Please fetch first.",
                color="warning",
                className="mt-3 mb-3"
            ),
            id=K.div.noDataAlert,
            style={"display": "none"}
        ),

        dbc.Spinner(
            htm.Div(id=K.div.grid, className="mb-4"),
            color="primary",
            type="border",
            spinner_style={"width": "3rem", "height": "3rem"}
        ),

        # Pagination
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Previous",
                    id=K.div.btnPrevPage,
                    color="primary",
                    disabled=True,
                    className="w-100"
                )
            ], width=4),

            dbc.Col([
                htm.Div([
                    htm.Span("Page: "),
                    dbc.Input(
                        id=K.div.currentPage,
                        type="number",
                        min=1,
                        value=1,
                        style={"width": "80px", "display": "inline-block"},
                        className="mx-2"
                    ),
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

        dcc.Store(id=K.div.paginationStore, data={"page": 1, "per_page": 24, "total": 0}),

        #====== bottom end ======================================================
    ])

#========================================================================
# Page initialization
#========================================================================
@callback(
    [
        out(K.inp.selectUserId, "options"),
        out(K.div.noDataAlert, "style"),
        out(K.div.paginationStore, "data"),
    ],
    inp(ks.sto.now, "data"),
    prevent_initial_call=False
)
def viewGrid_Init(dta_now):
    now = models.Now.fromStore(dta_now)

    user_options = [{"label": "All Users", "value": ""}]
    if now.usrs and len(now.usrs) > 0:
        for usr in now.usrs:
            user_options.append({"label": usr.name, "value": usr.id})

    show_alert = {"display": "block"} if now.cntPic <= 0 else {"display": "none"}

    pag_data = {"page": 1, "per_page": 24, "total": now.cntPic or 0}

    return user_options, show_alert, pag_data


#========================================================================
# Handle filter changes and pagination controls
#========================================================================
@callback(
    out(K.div.paginationStore, "data", allow_duplicate=True),
    [
        inp(K.inp.selectUserId, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.checkFavorites, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.selectPerPage, "value"),
        inp(K.div.btnNextPage, "n_clicks"),
        inp(K.div.btnPrevPage, "n_clicks"),
        inp(K.div.currentPage, "value"),
    ],
    [
        ste(K.div.paginationStore, "data"),
        ste(K.inp.selectUserId, "value"),
        ste(K.inp.selectFilter, "value"),
        ste(K.inp.checkFavorites, "value"),
        ste(K.inp.searchKeyword, "value"),
    ],
    prevent_initial_call=True
)
def on_pagination_controls(
    userId, filterOption, favoritesOnly, searchKeyword, perPage,
    nextClicks, prevClicks, currentPage,
    pag_data, stateUserId, stateFilterOption, stateFavoritesOnly, stateSearchKeyword
):
    trigger = getTriggerId()

    filter_triggers = [
        K.inp.selectUserId, K.inp.selectFilter,
        K.inp.checkFavorites, K.inp.searchKeyword,
        K.inp.selectPerPage
    ]

    if trigger in filter_triggers:
        pag_data["page"] = 1
        pag_data["per_page"] = perPage

        total = getTotalFilteredCount(
            usrId=userId,
            opts=filterOption,
            search=searchKeyword,
            favOnly=favoritesOnly
        )
        pag_data["total"] = total

        return pag_data

    page = pag_data["page"]
    per_page = pag_data["per_page"]
    total = pag_data["total"]

    total_pages = max(1, (total + per_page - 1) // per_page)

    if trigger == K.div.btnNextPage and nextClicks:
        page = min(page + 1, total_pages)
    elif trigger == K.div.btnPrevPage and prevClicks:
        page = max(1, page - 1)
    elif trigger == K.div.currentPage:
        page = max(1, min(currentPage, total_pages)) if currentPage else 1

    pag_data["page"] = page

    return pag_data


#========================================================================
# Handle photo grid loading
#========================================================================
@callback(
    [
        out(K.div.grid, "children"),
        out(K.div.pagination, "children"),
        out(K.div.currentPage, "value"),
        out(K.div.currentPage, "max"),
        out(K.div.btnPrevPage, "disabled"),
        out(K.div.btnNextPage, "disabled"),
    ],
    [
        inp(K.div.paginationStore, "data"),
        inp(K.inp.selectUserId, "value"),
        inp(K.inp.selectSortBy, "value"),
        inp(K.inp.selectSortOrder, "value"),
        inp(K.inp.selectFilter, "value"),
        inp(K.inp.searchKeyword, "value"),
        inp(K.inp.checkFavorites, "value"),
    ],
    ste(ks.sto.now, "data"),
    prevent_initial_call=False
)
def viewGrid_Load(pag_data, userId, sortBy, sortOrd, filOpt, shKey, onlyFav, dta_now):
    now = models.Now.fromStore(dta_now)

    page = pag_data["page"]
    pageSize = pag_data["per_page"]
    total = pag_data["total"]

    if now.cntPic <= 0: return htm.Div("No photos available"), "0", 1, 1, True, True

    total_pages = max(1, (total + pageSize - 1) // pageSize)

    pageIdx = min(total_pages, max(1, page))

    photos = getFilteredAssets(userId, sortBy, sortOrd, filOpt, shKey, onlyFav, pageIdx, pageSize)

    if photos and len(photos) > 0:
        lg.info(f"Loaded {len(photos)} photos")
    else:
        lg.info("No photos loaded")

    grid = createGrid(photos)

    prev_disabled = pageIdx <= 1
    next_disabled = pageIdx >= total_pages

    return grid, f"{total_pages}", pageIdx, total_pages, prev_disabled, next_disabled


#========================================================================
# Helper Functions
#========================================================================
def getFilteredAssets(
    usrId="", sort="fileCreatedAt", sortOrd="desc",
    opts="all", search="", onlyFav=False,
    page=1, pageSize=24
) -> list[models.Asset]:
    try:
        conditions = []
        params = []

        if usrId:
            conditions.append("ownerId = ?")
            params.append(usrId)

        if onlyFav:
            conditions.append("isFavorite = 1")

        if opts == "with_vectors":
            conditions.append("isVectored = 1")
        elif opts == "without_vectors":
            conditions.append("isVectored = 0")

        if search and len(search.strip()) > 0:
            conditions.append("originalFileName LIKE ?")
            params.append(f"%{search}%")

        query = "Select * From assets"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY {sort} {'DESC' if sortOrd == 'desc' else 'ASC'}"
        query += f" LIMIT {pageSize} OFFSET {(page - 1) * pageSize}"

        conn = db.pics.getConn()
        cursor = conn.cursor()
        cursor.execute(query, params)

        assets = []
        for row in cursor.fetchall():
            asset = models.Asset.fromDB(cursor, row)
            assets.append(asset)

        return assets
    except Exception as e:
        lg.error(f"Error fetching photos: {str(e)}")
        return []


def getTotalFilteredCount(usrId="", opts="all", search="", favOnly=False):
    try:
        conditions = []
        params = []

        if usrId:
            conditions.append("ownerId = ?")
            params.append(usrId)

        if favOnly:
            conditions.append("isFavorite = 1")

        if opts == "with_vectors":
            conditions.append("isVectored = 1")
        elif opts == "without_vectors":
            conditions.append("isVectored = 0")

        if search and len(search.strip()) > 0:
            conditions.append("originalFileName LIKE ?")
            params.append(f"%{search}%")

        query = "Select Count(*) From assets"
        if conditions: query += " WHERE " + " AND ".join(conditions)

        conn = db.pics.getConn()
        cursor = conn.cursor()
        cursor.execute(query, params)

        return cursor.fetchone()[0]
    except Exception as e:
        lg.error(f"Error counting photos: {str(e)}")
        return 0
