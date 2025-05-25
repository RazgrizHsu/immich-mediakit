from typing import List, Any, Optional, Union
from dsh import htm, dcc, dbc, callback, inp, out, ste, ctx, ALL, MATCH
from mod.models import Taber, Tab
from util import log

lg = log.get(__name__)


class k:
    tab = "taber-tab"
    store = "taber-store"

# noinspection PyShadowingBuiltins
class id:
    @staticmethod
    def store(dstId):
        return {"type": k.store, "id": dstId}


def createTaber(tabId: str, tabs: List[Union[Tab, str, List[Any]]], tabActs: List[Any] = None, contents: List[Any] = None) -> List[Any]:
    """
    Create a taber component with necessary stores

    Args:
        tabId: Unique identifier for the taber
        tabs: List of Tab models, strings, or lists of components
              - Tab: Use as is
              - str: Create Tab with string as title
              - List: Create Tab with components as title
        tabActs: List of actions for right side of tab header
        contents: List of content divs corresponding to each tab

    Returns:
        List of components including taber div and store
    """

    # Process tabs - ensure they have IDs and indices
    toTabs = []
    tab_contents = []  # Store the actual content for each tab

    # Check if any Tab has active=True
    hasAv = any(isinstance(t, Tab) and t.active for t in tabs)

    for i, inp in enumerate(tabs):
        if isinstance(inp, Tab):
            # Tab object - create a copy to avoid modifying the original
            tab_copy = Tab(
                title=inp.title,
                disabled=inp.disabled,
                active=inp.active,
                allowRefresh=inp.allowRefresh,
                id=inp.id or f"tab-{i}",  # Auto-generate ID if not provided
                _idx=i,  # Set index
                n_clicks=inp.n_clicks
            )
            tab_contents.append(inp.title)
        elif isinstance(inp, str):
            # String - create Tab with string as title
            tab_copy = Tab(
                title=inp,
                disabled=False,
                active=(i == 0 and not hasAv),  # First tab is active by default if none specified
                allowRefresh=False,
                id=f"tab-{i}",
                _idx=i,
                n_clicks=0
            )
            tab_contents.append(inp)
        elif isinstance(inp, list):
            # List of components - create Tab with placeholder title
            # The actual content will be rendered in nav_tabs
            tab_copy = Tab(
                title="",  # Empty title, will use components instead
                disabled=False,
                active=(i == 0 and not hasAv),  # First tab is active by default if none specified
                allowRefresh=False,
                id=f"tab-{i}",
                _idx=i,
                n_clicks=0
            )
            tab_contents.append(inp)
        else:
            # Unknown type - treat as string
            tab_copy = Tab(
                title=str(inp),
                disabled=False,
                active=(i == 0 and not hasAv),
                allowRefresh=False,
                id=f"tab-{i}",
                _idx=i,
                n_clicks=0
            )
            tab_contents.append(str(inp))

        toTabs.append(tab_copy)

    navs = []
    for tab, c in zip(toTabs, tab_contents):
        navs.append(
            htm.Div(
                c,
                className=tab.css(),
                id={"type": k.tab, "taber": tabId, "id": tab.id},
                n_clicks=tab.n_clicks
            )
        )

    body_contents = []
    if contents:
        # Normalize contents - ensure it's a list
        conts = []
        for c in contents: conts.append(c)

        for i, (tab, c) in enumerate(zip(toTabs, conts)):
            body_contents.append(
                htm.Div(
                    c,
                    id=f"{tabId}-content-{i}",  # Simple content ID based on index
                    className="act" if tab.active else ""
                )
            )

    divTaber = htm.Div([
        htm.Div([
            htm.Div(navs, className="nav"),
            htm.Div(tabActs, className="acts") if tabActs else None,
        ], className="head"),

        htm.Div(body_contents, className="body") if body_contents else None,
    ], className="taber", id=tabId)

    # Create initial taber model for store with processed tabs
    model = Taber(id=tabId, tabs=toTabs, tabActs=tabActs or [])

    return [
        divTaber,
        dcc.Store(id={"type": k.store, "id": tabId}, data=model.toDict())
    ]


def regCallbacks(tarId: str):
    """
    Register a callback for handling tab clicks for a specific taber instance.
    This function should be called after the layout is defined.

    Args:
        tarId: The ID of the taber component
    """

    @callback(
        [
            out({"type": k.store, "id": tarId}, "data"),
            out({"type": k.tab, "taber": tarId, "id": ALL}, "className"),
            out(tarId, "children"),
        ],
        inp({"type": k.tab, "taber": tarId, "id": ALL}, "n_clicks"),
        [
            ste({"type": k.store, "id": tarId}, "data"),
            ste(tarId, "children"),
        ],
        prevent_initial_call=True
    )
    def handle_tab_click(clks, dta_tab, tItems):
        if not dta_tab: return {}, [], tItems

        # 如果沒有點擊事件，返回當前狀態
        if not ctx.triggered or not ctx.triggered[0]["value"]:
            taber = Taber.fromDict(dta_tab)
            css = []
            for tab in taber.tabs: css.append(tab.css())
            return dta_tab, css, tItems

        # 解析資料
        taber = Taber.fromDict(dta_tab)

        # 找出被點擊的 tab
        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            tabId = ctx.triggered_id.get("id")

            # 檢查 tab 是否被禁用
            tab = taber.getTab(tabId)
            if tab and not tab.disabled:
                # 檢查是否點擊當前已經 active 的 tab
                if tab.active and not tab.allowRefresh:
                    lg.info(f"[taber] Ignoring click on already active tab: {tabId}")
                    # 返回當前狀態，避免重複渲染
                    css = []
                    for tab in taber.tabs:
                        #cnm = "act" if tab.active else ""
                        #if tab.disabled: cnm = (cnm + " disabled").strip() if cnm else "disabled"
                        css.append(tab.css())

                    lg.info(f"[taber] css[{css}]")
                    return dta_tab, css, tItems

                # 更新 active 狀態
                taber.setActive(tabId)
                lg.info(f"[taber] Tab clicked: {tabId}{' (refresh)' if tab.active else ''}")

        # 生成 className 列表
        css = []
        for tab in taber.tabs:
            css.append(tab.css())

        lg.info(f"[taber] update content, tab css[{css}]")

        if not tItems:
            lg.warn( "[taber] =====>>> No Data?" )
            return taber.toDict(), [], tItems

        if not isinstance(tItems, list):
            lg.warn( f"[taber] =====>>> Data not list? type({type(tItems)}): {tItems}" )
            return taber.toDict(), [], tItems


        # # 更新 body 內容的顯示狀態
        # for idx, c in enumerate(tItems):
        #
        #     lg.info( f"[taber][{idx}] c: {c}" )
        #
        #     if isinstance(c, dict) and "props" in c:
        #         if c["props"].get("className") == "body" and "children" in c["props"]:
        #             cc = c["props"]["children"]
        #             for idxC in range(min(len(cc), len(taber.tabs))):
        #                 if "props" in cc[idxC]:
        #                     cc[idxC]["props"]["className"] = "act" if taber.tabs[idxC].active else ""

        dicHead = tItems[0]

        lg.info( f"head: {len(dicHead)}" )

        dicBody = tItems[1]

        lg.info( f"body: {len(dicBody)}" )



        #return taber.toDict(), css, tItems
        return taber.toDict(), ['act', 'act', 'act'], tItems
