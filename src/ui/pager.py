from typing import List, Optional, Callable, Literal
import json

from dsh import htm, dbc, dcc, callback, out, inp, ste, ctx, ALL
from util import log
from mod import models

lg = log.get(__name__)

DEBUG = False

SYM_FIRST = "‹‹"
SYM_PREV = "‹"
SYM_NEXT = "›"
SYM_LAST = "››"
SYM_ELLIPSIS = "…"


class id:
    @staticmethod
    def store(pgrId: str) -> str:
        return f"{pgrId}-store"


def createStore(
    pgId: str,
    page: int = 1,
    size: int = 20,
    total: int = 0,
) -> List:
    """
    Create a pgr store component

    Args:
        pgId: Unique ID for this pgr instance
        page: Current page number (1-based)
        size: Items per page
        total: Total number of items

    Returns:
        List containing the store component
    """
    pgr = models.Pager(idx=page, size=size, cnt=total)
    return [

        dcc.Store(id=id.store(pgId), data=pgr.toDict(), storage_type="session"),
    ]


def createPager(pgId: str, idx: int = 0, className: str = None, showInfo: bool = True, avFirstLast: bool = True, avPrevNext: bool = True, btnSize: int = 7, page: int = 1, size: int = 20, total: int = 0) -> List:
    htms = _buildUI(
        pgrId=pgId,
        idx=idx,
        page=page,
        size=size,
        total=total,
        showInfo=showInfo,
        avFirstLast=avFirstLast,
        avPrevNext=avPrevNext,
        btnSize=btnSize
    )

    return [
        dcc.Store(
            id={"type": f"pgr-{pgId}-store", "idx": idx},
            data={
                "showInfo": showInfo,
                "avFirstLast": avFirstLast,
                "avPrevNext": avPrevNext,
                "btnSize": btnSize
            }
        ),
        htm.Div(
            htms,
            id={"type": f"pgr-{pgId}-container", "idx": idx},
            className=className
        )
    ]


def _buildUI(pgrId: str, idx: int, page: int, size: int, total: int, btnSize: int = 5, avFirstLast: bool = True, avPrevNext: bool = True, showInfo: bool = False) -> List:

    totalPages = (total + size - 1) // size if total > 0 else 1
    page = max(1, min(page, totalPages))

    if total <= 0: return []

    items = []

    if avFirstLast:
        items.append(htm.Li(
            htm.A(
                SYM_FIRST,
                className="lnk",
                id={"type": f"pgr-{pgrId}-nav", "action": "first", "idx": idx},


            ) if page > 1 else htm.Span(
                SYM_FIRST,
                className="lnk"
            ),
            className="item" + (" disabled" if page <= 1 else "")
        ))

    if avPrevNext:
        items.append(htm.Li(
            htm.A(SYM_PREV,
                  className="lnk",
                  id={"type": f"pgr-{pgrId}-nav", "action": "prev", "idx": idx},

                  ) if page > 1 else htm.Span(
                SYM_PREV
                ,
                className="lnk"
            ),
            className="item" + (" disabled" if page <= 1 else "")
        ))

    halfVisible = btnSize // 2
    startPage = max(1, page - halfVisible)
    endPage = min(totalPages, startPage + btnSize - 1)

    if endPage - startPage + 1 < btnSize:
        startPage = max(1, endPage - btnSize + 1)

    if startPage > 1:
        items.append(htm.Li(
            htm.A("1", className="lnk", id={"type": f"pgr-{pgrId}-page", "page": 1, "idx": idx}),
            className="item"
        ))
        if startPage > 2:
            items.append(htm.Li(
                htm.Span(SYM_ELLIPSIS, className="lnk"),
                className="item disabled"
            ))

    for p in range(startPage, endPage + 1):
        items.append(htm.Li(
            htm.A(
                str(p),
                className="lnk",
                id={"type": f"pgr-{pgrId}-page", "page": p, "idx": idx},

            ) if p != page else htm.Span(
                str(p),
                className="lnk"
            ),
            className="item" + (" active" if p == page else "")
        ))

    if endPage < totalPages:
        if endPage < totalPages - 1:
            items.append(htm.Li(
                htm.Span(
                    htm.Span(SYM_ELLIPSIS),
                    className="lnk"
                ),
                className="item disabled"
            ))
        items.append(htm.Li(
            htm.A(
                str(totalPages),
                className="lnk",
                id={"type": f"pgr-{pgrId}-page", "page": totalPages, "idx": idx},
            ),
            className="item"
        ))

    if avPrevNext:
        items.append(htm.Li(
            htm.A(
                SYM_NEXT,
                className="lnk",
                id={"type": f"pgr-{pgrId}-nav", "action": "next", "idx": idx},

            ) if page < totalPages else htm.Span(
                SYM_NEXT,
                className="lnk"
            ),
            className="item" + (" disabled" if page >= totalPages else "")
        ))

    if avFirstLast:
        items.append(htm.Li(
            htm.A(
                SYM_LAST,
                className="lnk",
                id={"type": f"pgr-{pgrId}-nav", "action": "last", "idx": idx},

            ) if page < totalPages else htm.Span(
                SYM_LAST,
                className="lnk"
            ),
            className="item" + (" disabled" if page >= totalPages else "")
        ))

    components = [
        htm.Ul(
            items,
            id=f"{pgrId}-{idx}",
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


def regCallbacks(pgrId: str, onPageChg: Optional[Callable] = None):
    lg.info( f"[pager] registering callbacks for {pgrId}" )

    # Handle page clicks
    @callback(
        out(id.store(pgrId), "data"),
        [
            inp({"type": f"pgr-{pgrId}-page", "page": ALL, "idx": ALL}, "n_clicks"),
            inp({"type": f"pgr-{pgrId}-nav", "action": ALL, "idx": ALL}, "n_clicks")
        ],
        ste(id.store(pgrId), "data"),
        prevent_initial_call=True
    )
    def pager_onClick(clks_pg, clks_nv, dta_pgr):
        if not ctx.triggered:
            return dta_pgr

        # Check if any actual click happened (not just initialization)
        if all(click is None for click in clks_pg + clks_nv):
            if DEBUG: lg.info(f"[pgr:{pgrId}] Ignoring initial callback with all None clicks")
            return dta_pgr

        if DEBUG: lg.info(f"[pgr:{pgrId}] onClick triggered: {ctx.triggered}, page_clicks: {clks_pg}, nav_clicks: {clks_nv}")

        pgr = models.Pager.fromDict(dta_pgr)

        # Ensure idx is valid (default to 1 if None)
        if pgr.idx is None:
            pgr.idx = 1

        totalPages = (pgr.cnt + pgr.size - 1) // pgr.size if pgr.cnt > 0 else 1

        triggered = ctx.triggered[0]
        prop_id = triggered["prop_id"]


        # Check if it's a page click or nav click
        if f"pgr-{pgrId}-page" in prop_id:
            # Direct page click
            trig_id = json.loads(prop_id.split(".")[0])
            newPage = trig_id["page"]
        elif f"pgr-{pgrId}-nav" in prop_id:
            # Navigation button click
            trig_id = json.loads(prop_id.split(".")[0])
            action = trig_id["action"]

            if action == "first":
                newPage = 1
            elif action == "last":
                newPage = totalPages
            elif action == "prev":
                newPage = max(1, pgr.idx - 1) if pgr.idx else 1
            elif action == "next":
                newPage = min(totalPages, pgr.idx + 1) if pgr.idx else 2
            else:
                return dta_pgr
        else:
            return dta_pgr

        # Update pgr
        pgr.idx = newPage

        if DEBUG: lg.info(f"[pgr:{pgrId}] Page changed to {newPage}/{totalPages}")

        # Call custom callback if provided
        if onPageChg:
            try:
                onPageChg(pgr)
            except Exception as e:
                lg.error(f"[pgr:{pgrId}] Error in onPageChange callback: {e}")

        return pgr.toDict()


    #------------------------------------------------------------------------
    # Update pager UI when store changes
    #------------------------------------------------------------------------
    @callback(
        out({"type": f"pgr-{pgrId}-container", "idx": ALL}, "children"),
        [
            inp(id.store(pgrId), "data"),
            ste({"type": f"pgr-{pgrId}-store", "idx": ALL}, "data")
        ],
        prevent_initial_call=False
    )
    def pager_updateUI(dta_pgr, dta_bars):

        if DEBUG: lg.info(f"[pgr:{pgrId}] updateUI data[{dta_pgr}] bar count[{len(dta_bars)}]")

        if not dta_pgr:
            if DEBUG: lg.info(f"[pgr:{pgrId}] NoStore, RetEmpty")
            return [[] for _ in dta_bars]

        pgr = models.Pager.fromDict(dta_pgr)
        if DEBUG: lg.info(f"[pgr:{pgrId}] pgr: page={pgr.idx}, size={pgr.size}, total={pgr.cnt}")

        results = []
        for idx, pgr_store in enumerate(dta_bars):
            if DEBUG: lg.info(f"[pgr:{pgrId}] processing idx={idx}, pgr_store={pgr_store}")
            if not pgr_store:
                if DEBUG: lg.info(f"[pgr:{pgrId}] idx={idx} has no pgr_store, appending empty")
                results.append([])
                continue

            ui_components = _buildUI(
                pgrId=pgrId,
                idx=idx,
                page=pgr.idx,
                size=pgr.size,
                total=pgr.cnt,
                showInfo=pgr_store.get("showInfo", False),
                avFirstLast=pgr_store.get("avFirstLast", True),
                avPrevNext=pgr_store.get("avPrevNext", True),
                btnSize=pgr_store.get("btnSize", 5)
            )
            results.append(ui_components)

        return results

    if DEBUG: lg.info(f"[pgr:{pgrId}] Callbacks registered with pattern matching")
