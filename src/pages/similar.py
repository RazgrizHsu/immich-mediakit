import db
from conf import Ks
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId
from util import log, models

lg = log.get(__name__)

dash.register_page(
    __name__,
    path=f'/{Ks.pgs.findDups}',
    title='Similar',
    name='Similar'
)

class K:
    class inp:
        selectUserId = "inp-dup-user-selector"
        sliderThresholdMin = "inp-dup-threshold-min"
        sliderThresholdMax = "inp-dup-threshold-max"
        selectSimilarityMethod = "inp-dup-similarity-method"
        selectCompareCount = "inp-dup-compare-count"
        selectSourceImage = "inp-dup-source-image"

    class div:
        btnFindDuplicates = "btn-find-duplicates"
        btnClearResults = "btn-clear-results"
        resultContainer = "div-dup-result-container"
        noDataAlert = "div-dup-no-data-alert"
        loadingIndicator = "div-dup-loading"
        pairwiseResults = "div-dup-pairwise-results"
        similarToSource = "div-dup-similar-to-source"
        resultStats = "div-dup-result-stats"
        resultStore = "store-dup-results"


#========================================================================
def layout():
    return htm.Div([
        htm.H3("Similar", className="mb-4"),

        htm.Div([
            htm.P(
                "Find similar photos based on image content. This uses AI-generated vector embeddings to find visually similar assets.",
                className="mb-4"
            ),

            dbc.Card([
                dbc.CardHeader("Search Settings"),
                dbc.CardBody([
                    dbc.Row([
                        # User filter
                        dbc.Col([
                            dbc.Label("User"),
                            dcc.Dropdown(
                                id=K.inp.selectUserId,
                                options=[{"label": "All Users", "value": ""}],
                                value="",
                                clearable=False,
                                className="mb-3"
                            ),
                        ], width=4),

                        # Similarity method
                        dbc.Col([
                            dbc.Label("Similarity Method"),
                            dcc.Dropdown(
                                id=K.inp.selectSimilarityMethod,
                                options=[
                                    {"label": "Cosine Similarity", "value": "cosine"},
                                    {"label": "Euclidean Distance", "value": "euclidean"}
                                ],
                                value="cosine",
                                clearable=False,
                                className="mb-3"
                            ),
                        ], width=4),

                        # Max results
                        dbc.Col([
                            dbc.Label("Max Comparisons"),
                            dcc.Dropdown(
                                id=K.inp.selectCompareCount,
                                options=[
                                    {"label": "100", "value": 100},
                                    {"label": "500", "value": 500},
                                    {"label": "1000", "value": 1000},
                                    {"label": "5000", "value": 5000}
                                ],
                                value=100,
                                clearable=False,
                                className="mb-3"
                            ),
                        ], width=4),
                    ]),

                    dbc.Row([
                        # Threshold range
                        dbc.Col([
                            dbc.Label("Similarity Threshold Range"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.RangeSlider(
                                        id=K.inp.sliderThresholdMin,
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        marks={
                                            0: "0",
                                            0.2: "0.2",
                                            0.4: "0.4",
                                            0.6: "0.6",
                                            0.8: "0.8",
                                            0.9: "0.9",
                                            0.95: "0.95",
                                            1: "1"
                                        },
                                        value=[0.9, 0.99],
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ])
                        ], width=12),
                    ]),

                    dbc.Row([
                        # Source image selection (optional)
                        dbc.Col([
                            dbc.Label("Source Image (Optional)"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(
                                        id=K.inp.selectSourceImage,
                                        type="text",
                                        placeholder="Enter image ID to find similar photos",
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ])
                        ], width=12),
                    ]),
                ])
            ], className="mb-4"),

            # No data alert
            htm.Div(
                dbc.Alert(
                    "No vector data available. Please process photos to generate vectors first.",
                    color="warning",
                    className="mt-3 mb-3"
                ),
                id=K.div.noDataAlert,
                style={"display": "none"}
            ),

            # Operation buttons
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Find Similar",
                        id=K.div.btnFindDuplicates,
                        color="primary",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),

                dbc.Col([
                    dbc.Button(
                        "Clear Results",
                        id=K.div.btnClearResults,
                        color="danger",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),
            ], className="mb-4"),

            # Results statistics
            htm.Div(id=K.div.resultStats, className="mb-4"),

            # Results container with tabs for different view modes
            dbc.Tabs([
                dbc.Tab([
                    dbc.Spinner(
                        htm.Div(id=K.div.pairwiseResults, className="mt-4"),
                        color="primary",
                        type="border",
                        spinner_style={"width": "3rem", "height": "3rem"}
                    )
                ], label="Duplicate Pairs", tab_id="tab-pairs"),

                dbc.Tab([
                    dbc.Spinner(
                        htm.Div(id=K.div.similarToSource, className="mt-4"),
                        color="primary",
                        type="border",
                        spinner_style={"width": "3rem", "height": "3rem"}
                    )
                ], label="Similar to Source", tab_id="tab-source", disabled=True),
            ], id=K.div.resultContainer, active_tab="tab-pairs"),

            dcc.Store(id=K.div.resultStore, data={"pairs": [], "similar": [], "has_results": False})
        ]),
    ])


#========================================================================
# callbacks
#========================================================================
@callback(
    [
        out(K.inp.selectUserId, "options"),
        out(K.div.noDataAlert, "style"),
        out(K.div.btnFindDuplicates, "disabled"),
        out(K.div.btnClearResults, "disabled"),
        out(K.div.resultContainer, "active_tab"),
        out("tab-source", "disabled"),
        out(K.div.resultStore, "data"),
        out(K.div.resultStats, "children"),
    ],
    [
        inp(Ks.store.now, "data"),
        inp(K.inp.selectSourceImage, "value"),
        inp(K.div.btnFindDuplicates, "n_clicks"),
        inp(K.div.btnClearResults, "n_clicks"),
    ],
    [
        ste(K.div.resultStore, "data"),
        ste(K.inp.selectUserId, "value"),
        ste(K.inp.sliderThresholdMin, "value"),
        ste(K.inp.selectSimilarityMethod, "value"),
        ste(K.inp.selectCompareCount, "value"),
    ],
    prevent_initial_call=False
)
def manage_page_state(dta_now, source_id, find_clicks, clear_clicks,
    result_data, userId, threshold_range, similarity_method, compare_count):
    trigger = getTriggerId()

    empty_results = {"pairs": [], "similar": [], "has_results": False}
    no_stats = htm.Div()
    now = models.Now.fromStore(dta_now)

    user_options = [{"label": "All Users", "value": ""}]
    if now.usrs and len(now.usrs) > 0:
        for usr in now.usrs:
            user_options.append({"label": usr.name, "value": usr.id})

    has_vectors = now.cntVec > 0
    show_alert = {"display": "block"} if not has_vectors else {"display": "none"}

    has_source = source_id is not None and source_id.strip() != ""
    has_similar_results = result_data and len(result_data.get("similar", [])) > 0
    source_tab_disabled = not has_source

    if trigger == K.div.btnClearResults and clear_clicks:
        result_data = empty_results
        btn_clear_disabled = True
        btn_find_disabled = not has_vectors
        active_tab = "tab-pairs"
        return (user_options, show_alert, btn_find_disabled, btn_clear_disabled,
                active_tab, source_tab_disabled, result_data, no_stats)

    elif trigger == K.div.btnFindDuplicates and find_clicks:
        if not has_vectors:
            return (user_options, show_alert, True, True, "tab-pairs", source_tab_disabled,
                    empty_results, htm.Div(dbc.Alert("No vector data available", color="danger")))

        min_threshold, max_threshold = threshold_range

        results = {"pairs": [], "similar": [], "has_results": False}

        if has_source:
            source_id_clean = source_id.strip()
            similar_photos = db.vecs.find_similar_photos(
                photo_id=source_id_clean,
                min_threshold=min_threshold,
                max_threshold=max_threshold,
                limit=compare_count,
                similarity_method=similarity_method
            )

            if similar_photos:
                similar_results = []
                for id1, id2, score in similar_photos:
                    other_id = id2 if id1 == source_id_clean else id1
                    similar_results.append({
                        "source_id": source_id_clean,
                        "similar_id": other_id,
                        "similarity": score
                    })

                results["similar"] = similar_results
                results["has_results"] = True

        photos_with_vectors = get_photos_with_vectors(userId)

        if len(photos_with_vectors) > 0:
            duplicate_pairs = find_duplicate_pairs(
                photos=photos_with_vectors,
                min_threshold=min_threshold,
                max_threshold=max_threshold,
                max_comparisons=compare_count,
                similarity_method=similarity_method
            )

            if duplicate_pairs:
                results["pairs"] = duplicate_pairs
                results["has_results"] = True

        if results["has_results"]:
            pair_count = len(results["pairs"])
            similar_count = len(results["similar"])

            stats_children = []

            if pair_count > 0:
                stats_children.append(
                    dbc.Alert(f"Found {pair_count} potential duplicate pairs", color="success", className="mb-2")
                )

            if similar_count > 0:
                stats_children.append(
                    dbc.Alert(f"Found {similar_count} photos similar to source image", color="info")
                )

            stats_div = htm.Div(stats_children)

            active_tab = "tab-source" if has_source and similar_count > 0 else "tab-pairs"

            return (user_options, show_alert, not has_vectors, False, active_tab,
                    source_tab_disabled, results, stats_div)
        else:
            no_results_alert = dbc.Alert(
                "No duplicate photos found with current threshold settings",
                color="warning"
            )
            return (user_options, show_alert, not has_vectors, True, "tab-pairs",
                    source_tab_disabled, empty_results, htm.Div(no_results_alert))

    else:
        btn_clear_disabled = not (result_data and result_data.get("has_results", False))
        btn_find_disabled = not has_vectors

        active_tab = "tab-source" if has_source and has_similar_results else "tab-pairs"

        if result_data and result_data.get("has_results", False):
            pair_count = len(result_data.get("pairs", []))
            similar_count = len(result_data.get("similar", []))

            stats_children = []

            if pair_count > 0:
                stats_children.append(
                    dbc.Alert(f"Found {pair_count} potential duplicate pairs", color="success", className="mb-2")
                )

            if similar_count > 0:
                stats_children.append(
                    dbc.Alert(f"Found {similar_count} photos similar to source image", color="info")
                )

            stats_div = htm.Div(stats_children)
        else:
            stats_div = no_stats

        return (user_options, show_alert, btn_find_disabled, btn_clear_disabled,
                active_tab, source_tab_disabled, result_data, stats_div)


#========================================================================
# Display duplicate pair results
#========================================================================
@callback(
    out(K.div.pairwiseResults, "children"),
    inp(K.div.resultStore, "data"),
    prevent_initial_call=False
)
def display_pairwise_results(result_data):
    if not result_data or not result_data.get("has_results") or not result_data.get("pairs"):
        return htm.Div("No duplicate pairs found.", className="text-center p-4")

    pairs = result_data.get("pairs", [])
    if not pairs:
        return htm.Div("No duplicate pairs found.", className="text-center p-4")

    pairs.sort(key=lambda x: x["similarity"], reverse=True)

    pair_cards = []
    for i, pair in enumerate(pairs):
        card = create_pair_card(
            photo1_id=pair["photo1_id"],
            photo2_id=pair["photo2_id"],
            similarity=pair["similarity"],
            index=i + 1
        )
        pair_cards.append(card)

    return htm.Div(pair_cards)


#========================================================================
# Display similar to source results
#========================================================================
@callback(
    out(K.div.similarToSource, "children"),
    inp(K.div.resultStore, "data"),
    prevent_initial_call=False
)
def display_similar_results(result_data):
    if not result_data or not result_data.get("has_results") or not result_data.get("similar"):
        return htm.Div("No similar photos found for the source image.", className="text-center p-4")

    similar = result_data.get("similar", [])
    if not similar:
        return htm.Div("No similar photos found for the source image.", className="text-center p-4")

    similar.sort(key=lambda x: x["similarity"], reverse=True)

    source_id = similar[0]["source_id"]
    source_photo = get_photo_details(source_id)

    source_card = dbc.Card([
        dbc.CardHeader("Source Photo"),
        dbc.CardBody([
            create_photo_card(source_photo, "Source")
        ])
    ], className="mb-4")

    similar_cards = []
    for i, item in enumerate(similar):
        similar_photo = get_photo_details(item["similar_id"])

        card = dbc.Card([
            dbc.CardHeader(f"Similar Photo #{i + 1} - Similarity: {item['similarity']:.4f}"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(create_photo_card(source_photo, "Source"), width=6),
                    dbc.Col(create_photo_card(similar_photo, "Similar"), width=6),
                ])
            ])
        ], className="mb-3")

        similar_cards.append(card)

    return htm.Div([source_card, htm.Div(similar_cards)])


#========================================================================
# Helper Functions
#========================================================================
def get_photos_with_vectors(userId=None):
    try:
        conn = db.pics.mkconn()
        cursor = conn.cursor()

        query = "Select * From assets Where isVectored = 1"
        params = []

        if userId:
            query += " AND ownerId = ?"
            params.append(userId)

        cursor.execute(query, params)

        photos = []
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            photo = dict(zip(columns, row))
            photos.append(photo)

        return photos
    except Exception as e:
        lg.error(f"Error getting photos with vectors: {str(e)}")
        return []


def find_duplicate_pairs(photos, min_threshold, max_threshold, max_comparisons=100, similarity_method="cosine"):
    duplicate_pairs = []
    processed_pairs = set()

    max_photos = min(len(photos), max_comparisons)
    photos_to_check = photos[:max_photos]

    for i, photo in enumerate(photos_to_check):
        photo_id = photo.get('id')

        similar_photos = db.vecs.find_similar_photos(
            photo_id=photo_id,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            limit=max_comparisons,
            similarity_method=similarity_method
        )

        for id1, id2, score in similar_photos:
            pair_key = tuple(sorted([id1, id2]))

            if pair_key in processed_pairs: continue

            processed_pairs.add(pair_key)

            duplicate_pairs.append({
                "photo1_id": id1,
                "photo2_id": id2,
                "similarity": score
            })

    return duplicate_pairs


def get_photo_details(photo_id):
    try:
        return db.pics.getAssetInfo(photo_id)
    except Exception as e:
        lg.error(f"Error getting photo details: {str(e)}")
        return None


def create_pair_card(photo1_id, photo2_id, similarity, index):
    photo1 = get_photo_details(photo1_id)
    photo2 = get_photo_details(photo2_id)

    if not photo1 or not photo2:
        return htm.Div(f"Error loading photo details (IDs: {photo1_id}, {photo2_id})")

    return dbc.Card([
        dbc.CardHeader(f"Duplicate Pair #{index} - Similarity: {similarity:.4f}"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(create_photo_card(photo1, "Photo 1"), width=6),
                dbc.Col(create_photo_card(photo2, "Photo 2"), width=6),
            ])
        ])
    ], className="mb-3")


def create_photo_card(photo:models.Asset, label):
    if not photo: return htm.Div("Photo not found")

    thumbnail_path = photo.thumbnail_path
    preview_path = photo.preview_path
    fullsize_path = photo.fullsize_path

    image_path = thumbnail_path or preview_path or fullsize_path or ""

    photo_id = photo.id
    filename = photo.originalFileName
    created_date = photo.fileCreatedAt

    return dbc.Card([
        dbc.CardHeader(label),
        dbc.CardImg(
            src=image_path,
            top=True,
            style={"height": "200px", "objectFit": "contain"}
        ),
        dbc.CardBody([
            htm.H5(
                filename,
                className="card-title text-truncate",
                title=filename,
                style={"fontSize": "0.9rem"}
            ),
            htm.P(
                f"ID: {photo_id[:8]}...",
                className="card-text small",
                style={"fontSize": "0.8rem"}
            ),
            htm.P(
                created_date,
                className="card-text small",
                style={"fontSize": "0.8rem"}
            ),
            dbc.Button(
                "View FullSize",
                color="primary",
                size="sm",
                className="mt-2",
                href=fullsize_path,
                target="_blank"
            )
        ], className="p-2")
    ], className="h-100")
