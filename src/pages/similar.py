import db
from conf import Ks
from dsh import dash, htm, dcc, callback, dbc, inp, out, ste, getTriggerId, ALL, noUpd
import traceback
import json
import flask
from util import log, models, task
from ui import gridSimilar as gvs
lg = log.get(__name__)

dash.register_page(
    __name__,
    title='Similar',
    name='Similar',
    path=f'/{Ks.pgs.similar}',
    path_template=f'/{Ks.pgs.similar}/<assetId>',
)

class k:
    storeAssId = "store-init-id"
    txtCntOk = 'txt-cnt-ok'
    txtCntNo = 'txt-cnt-no'
    class inp:
        sldThMin = "inp-dup-threshold-min"
        sldThMax = "inp-dup-threshold-max"
        useSimMth = "inp-dup-similarity-method"

    class div:
        btnFind = "btn-find-duplicates"
        btnClear = "btn-clear-results"
        btnDel = "btn-delete-selected"
        divRst = "div-dup-result-container"
        divNoData = "div-dup-no-data-alert"
        loading = "div-dup-loading"
        pairwiseResults = "div-dup-pairwise-results"
        allMatchedPhotos = "div-all-matched-photos"
        resultStats = "div-dup-result-stats"

        storeRst = "store-dup-results"
        storeSelectId = "store-selected-images"
        pager = "div-pagination-container"
        grid = "div-photo-grid"


#========================================================================
def layout(assetId=None, **kwargs):

    if False:
        return flask.redirect('/target-page')

    def mka( aid=0 ):
        ret = models.Asset.fromStore({ "id":f"{aid}" })
        return ret

    def mk( ass ):
        return gvs.create_photo_card(ass, f"lb")

    def createGV():
        ass = [
            mka(1), mka(2), mka(3), mka(4), mka(5), mka(6), mka(7),
        ]
        return gvs.createGrid( ass, mk, 260 )

    return htm.Div([

        dbc.Row([
            dbc.Col(htm.H3("Find Similar"), width=3),
            dbc.Col(htm.Small("Find similar photos based on image content. This uses AI-generated vector embeddings to find visually similar assets", className="text-muted"))
        ], className="mb-4"),

        htm.Div([

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("System Search Status"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(htm.Small("Searched", className="d-inline-block me-2"), width=5),
                                dbc.Col(dbc.Alert(f"0", color="info", className="py-1 px-2 mb-2 text-center")),
                            ]),
                            dbc.Row([
                                dbc.Col(htm.Small("Unsearched", className="d-inline-block me-2"), width=5),
                                dbc.Col(dbc.Alert(f"0", color="info", className="py-1 px-2 mb-2 text-center")),
                            ]),
                            dbc.Row([htm.Small("Shows vectorized data in the local db and whether similarity comparison has been performed with other assets", className="text-muted")])
                        ])
                    ], className="mb-4"),
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Search Settings"),
                        dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Similarity Method", className="txt-sm"),
                            dcc.Dropdown(
                                id=k.inp.useSimMth,
                                options=[
                                    {"label": "Cosine Similarity", "value": "cosine"},
                                    {"label": "Euclidean Distance", "value": "euclidean"}
                                ],
                                value="cosine",
                                clearable=False,
                                className="mb-3"
                            ),
                        ]),
                    ]),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Similarity Threshold Range", className="txt-sm"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.RangeSlider(
                                        id=k.inp.sldThMin,
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        marks=Ks.defs.thMarks,
                                        value=[0.8, 0.99],
                                        className="mb-0"
                                    ),
                                ], className="mt-2"),
                            ])
                        ]),
                    ]),
                ])
            ], className="mb-0")
                ], width=8),
            ], className="mb-1"),

            # No data alert
            htm.Div(
                dbc.Alert(
                    "No vector data available. Please process photos to generate vectors first.",
                    color="warning",
                    className="mt-3 mb-3"
                ),
                id=k.div.divNoData,
                style={"display": ""}
            ),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Find Similar",
                        id=k.div.btnFind,
                        color="primary",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),

                dbc.Col([
                    dbc.Button(
                        "Clear Results",
                        id=k.div.btnClear,
                        color="danger",
                        size="lg",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=6),
            ], className="mb-4"),


            # Results statistics
            htm.Div(id=k.div.resultStats, className="mb-4"),

            # Selected photos info and delete button
            dbc.Row([
                dbc.Col([
                    htm.Div(id="selected-count", className="h4 mb-3"),
                ], width=8),

                dbc.Col([
                    dbc.Button(
                        "Delete Selected",
                        id=k.div.btnDel,
                        color="danger",
                        size="md",
                        className="w-100",
                        disabled=True,
                    ),
                ], width=4),
            ], className="mt-4 mb-3", id="selected-photos-container", style={"display": ""}),


            # Results container with tabs
            dbc.Tabs([
                dbc.Tab([
                    htm.Div([

                        dbc.Row([
                            dbc.Col([
                                dbc.Pagination( id=k.div.pager,active_page=7, min_value=1, max_value=99, first_last=True, previous_next=True,fully_expanded=False,style={"display": ""})
                            ], className="d-flex justify-content-center mb-3")
                        ]),

                        htm.Div([
                            createGV(),
                        ], id=k.div.grid, className="mb-4"),

                        dbc.Spinner(
                            htm.Div(id=k.div.pairwiseResults, className="mt-2"),
                            color="primary",
                            type="border",
                            spinner_style={"width": "3rem", "height": "3rem"}
                        )
                    ])
                ], label="Duplicate Pairs", tab_id="tab-pairs"),
            ], id=k.div.divRst, active_tab="tab-pairs"),

            dcc.Store(id=k.div.storeRst, data={"pairs": [], "has_results": False}),
            dcc.Store(id=k.div.storeSelectId, data={"selected_images": []}),
            dcc.Store(id="search_in_progress", data={"in_progress": False}),
            dcc.Store(id=k.storeAssId, data=assetId)
        ]),
    ])

