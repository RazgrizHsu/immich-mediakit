from typing import List, Optional, Callable
from dsh import htm, dbc, dcc, callback, out, inp, ste, ctx, ALL
from util import log
from mod import models

lg = log.get(__name__)


class id:
    @staticmethod
    def store(pagerId: str) -> str:
        return f"{pagerId}-store"


def createStore(
    pagerId: str,
    page: int = 1,
    size: int = 20,
    total: int = 0
) -> List:
    """
    Create a pager store component

    Args:
        pagerId: Unique ID for this pager instance
        page: Current page number (1-based)
        size: Items per page
        total: Total number of items

    Returns:
        List containing the store component
    """
    pgr = models.Pgr(idx=page, size=size, cnt=total)
    return [dcc.Store(id=id.store(pagerId), data=pgr.toDict())]


def createPager(
    pagerId: str,
    idx: int = 0,
    className: str = None,
) -> List:
    # Create empty container that will be populated by callbacks
    return [htm.Div(id=f"{pagerId}-{idx}-container", className=className)]


def _buildPagerUI(
    pagerId: str,
    idx: int,
    page: int,
    size: int,
    total: int,
    maxVisible: int = 5,
    showFirstLast: bool = True,
    showPrevNext: bool = True,
    showInfo: bool = False
) -> List:
    """
    Internal function to build pager UI components
    """
    # Calculate total pages
    totalPages = (total + size - 1) // size if total > 0 else 1
    page = max(1, min(page, totalPages))

    # If no data, return empty
    if total <= 0:
        return []

    # Build page items
    items = []

    # First button
    if showFirstLast:
        items.append(htm.Li(
            htm.A(
                htm.Span("«"),
                className="lnk",
                id={"type": f"{pagerId}-nav", "action": "first"},


            ) if page > 1 else htm.Span(
                htm.Span("«"),
                className="lnk"
            ),
            className="item" + (" disabled" if page <= 1 else "")
        ))

    # Previous button
    if showPrevNext:
        items.append(htm.Li(
            htm.A(htm.Span("‹"),
                  className="lnk",
                  id={"type": f"{pagerId}-nav", "action": "prev"},

                  ) if page > 1 else htm.Span(
                htm.Span("‹")
                ,
                className="lnk"
            ),
            className="item" + (" disabled" if page <= 1 else "")
        ))

    # Calculate page range
    halfVisible = maxVisible // 2
    startPage = max(1, page - halfVisible)
    endPage = min(totalPages, startPage + maxVisible - 1)

    if endPage - startPage + 1 < maxVisible:
        startPage = max(1, endPage - maxVisible + 1)

    # Add ellipsis at start if needed
    if startPage > 1:
        items.append(htm.Li(
            htm.A("1", className="lnk", id={"type": f"{pagerId}-page", "page": 1}),
            className="item"
        ))
        if startPage > 2:
            items.append(htm.Li(
                htm.Span("…", className="lnk"),
                className="item disabled"
            ))

    # Page number buttons
    for p in range(startPage, endPage + 1):
        items.append(htm.Li(
            htm.A(
                str(p),
                className="lnk",
                id={"type": f"{pagerId}-page", "page": p},

            ) if p != page else htm.Span(
                str(p),
                className="lnk"
            ),
            className="item" + (" active" if p == page else "")
        ))

    # Add ellipsis at end if needed
    if endPage < totalPages:
        if endPage < totalPages - 1:
            items.append(htm.Li(
                htm.Span(
                    htm.Span("…"),
                    className="lnk"
                ),
                className="item disabled"
            ))
        items.append(htm.Li(
            htm.A(
                str(totalPages),
                className="lnk",
                id={"type": f"{pagerId}-page", "page": totalPages},
            ),
            className="item"
        ))

    # Next button
    if showPrevNext:
        items.append(htm.Li(
            htm.A(
                htm.Span("›"),
                className="lnk",
                id={"type": f"{pagerId}-nav", "action": "next"},

            ) if page < totalPages else htm.Span(
                htm.Span("›"),
                className="lnk"
            ),
            className="item" + (" disabled" if page >= totalPages else "")
        ))

    # Last button
    if showFirstLast:
        items.append(htm.Li(
            htm.A(
                htm.Span("»"),
                className="lnk",
                id={"type": f"{pagerId}-nav", "action": "last"},

            ) if page < totalPages else htm.Span(
                htm.Span("»"),
                className="lnk"
            ),
            className="item" + (" disabled" if page >= totalPages else "")
        ))

    components = [
        htm.Ul(
            items,
            id=f"{pagerId}-{idx}",
            className="pager"
        )
    ]

    if showInfo:
        startItem = (page - 1) * size + 1
        endItem = min(page * size, total)
        components.append(
            htm.Div([
                htm.Span([
                    f"{startItem}-{endItem} of {total}",
                ])

            ],
                className="pager-info"
            )
        )

    return components


def regCallbacks(pagerId: str, onPageChg: Optional[Callable] = None, pagerIds: Optional[List[int]] = None):
    """
    Register callbacks for pager component

    Args:
        pagerId: The pager ID to register callbacks for
        onPageChg: Optional callback function when page changes
        pagerIds: List of pager indices to manage (default [0, 1] for top and bottom)
    """

    # Default to [0, 1] if not specified
    if pagerIds is None:
        pagerIds = [0, 1]

    # Handle page clicks
    @callback(
        out(id.store(pagerId), "data"),
        [
            inp({"type": f"{pagerId}-page", "page": ALL}, "n_clicks"),
            inp({"type": f"{pagerId}-nav", "action": ALL}, "n_clicks")
        ],
        ste(id.store(pagerId), "data"),
        prevent_initial_call=True
    )
    def pager_onClick(page_clicks, nav_clicks, store_data):
        if not ctx.triggered:
            return store_data

        pager = models.Pgr.fromDict(store_data)
        totalPages = (pager.cnt + pager.size - 1) // pager.size if pager.cnt > 0 else 1

        triggered = ctx.triggered[0]
        prop_id = triggered["prop_id"]

        # Parse triggered ID
        import json
        if "page" in prop_id:
            # Direct page click
            trig_id = json.loads(prop_id.split(".")[0])
            newPage = trig_id["page"]
        elif "nav" in prop_id:
            # Navigation button click
            trig_id = json.loads(prop_id.split(".")[0])
            action = trig_id["action"]

            if action == "first":
                newPage = 1
            elif action == "last":
                newPage = totalPages
            elif action == "prev":
                newPage = max(1, pager.idx - 1)
            elif action == "next":
                newPage = min(totalPages, pager.idx + 1)
            else:
                return store_data
        else:
            return store_data

        # Update pager
        pager.idx = newPage

        lg.info(f"[pager:{pagerId}] Page changed to {newPage}/{totalPages}")

        # Call custom callback if provided
        if onPageChg:
            try:
                onPageChg(pager)
            except Exception as e:
                lg.error(f"[pager:{pagerId}] Error in onPageChange callback: {e}")

        return pager.toDict()


    #------------------------------------------------------------------------
    # Update pager UI when store changes
    #------------------------------------------------------------------------
    if pagerIds:
        outputs = []
        for idx in pagerIds:
            outputs.append(out(f"{pagerId}-{idx}-container", "children"))

        @callback(
            outputs,
            inp(id.store(pagerId), "data"),
            prevent_initial_call=False
        )
        def pager_updateUI(store_data):
            if not store_data:
                return [[] for _ in pagerIds]

            pgr = models.Pgr.fromDict(store_data)

            results = []
            for idx in pagerIds:

                showInfo = (idx == 0)

                ui_components = _buildPagerUI(
                    pagerId=pagerId,
                    idx=idx,
                    page=pgr.idx,
                    size=pgr.size,
                    total=pgr.cnt,
                    showInfo=showInfo
                )
                results.append(ui_components)

            return results

    lg.info(f"[pager:{pagerId}] Callbacks registered for indices {pagerIds}")
