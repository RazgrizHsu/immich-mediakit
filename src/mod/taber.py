from typing import List, Any, Optional, Union
from dsh import htm, dcc, dbc, callback, inp, out, ste, ctx, ALL, noUpd
from mod.models import Taber, Tab
from util import log

lg = log.get(__name__)


class k:
    tab = "taber-tab"
    tabVw = "taber-tab-view"
    store = "taber-store"

# noinspection PyShadowingBuiltins
class id:
    @staticmethod
    def store(dstId):
        return {"type": k.store, "id": dstId}

    # @staticmethod
    # def view(dstId):
    #     return {"type": k.tabVw, "id": dstId}


def createTaber(tabId: str, defs: List[Union[Tab, str, List[Any]]], htmActs: List[Any] = None, tabBodies: List[Any] = None) -> List[Any]:
    """
    Create a taber component with necessary stores

    Args:
        tabId: Unique identifier for the taber
        defs: List of Tab models, strings, or lists of components
              - Tab: Use as is
              - str: Create Tab with string as title
              - List: Create Tab with components as title
        htmActs: List of actions for right side of tab header
        tabBodies: List of content divs corresponding to each tab

    Returns:
        List of components including taber div and store
    """

    # Process tabs - ensure they have IDs and indices
    tabs = []
    htmTabs = []

    anyAv = any(isinstance(t, Tab) and t.active for t in defs)

    for i, inp in enumerate(defs):
        if not isinstance(inp, Tab) and not isinstance(inp, str):
            raise TypeError(f"[taber] not supported type[{type(inp)}], tabs define only support models.Tab or string")

        tab = inp if isinstance(inp, Tab) else Tab(title=inp)

        if not anyAv and i == 0: tab.active = True  #default active

        tab.idx = i
        if not tab.id: tab.id = f"tab-{i}"

        tabs.append(tab)

        htmTabs.append(
            htm.Div(
                tab.title or "-no title-",
                id={"type": k.tab, "taber": tabId, "id": tab.id},
                className=tab.css(),
            )
        )



    htmBodies = []

    if tabBodies:
        conts = []
        for c in tabBodies: conts.append(c)

        for i, (tab, c) in enumerate(zip(tabs, conts)):
            htmBodies.append(
                htm.Div(
                    c,
                    id={"type": k.tabVw, "taber": tabId, "id": f"{tabId}-content-{i}"},
                    className="act" if tab.active else ""
                )
            )

    divTaber = htm.Div([
        htm.Div([
            htm.Div(htmTabs, className="nav"),
            htm.Div(htmActs, className="acts") if htmActs else None,
        ], className="head"),

        htm.Div(htmBodies, className="body") if htmBodies else None,
    ], className="taber", id=tabId)

    # Create initial taber model for store with processed tabs
    model = Taber(id=tabId, tabs=tabs)

    data = model.toDict()
    lg.info(f"[taber] data: {data}")

    return [
        divTaber,
        dcc.Store(id={"type": k.store, "id": tabId}, data=data)
    ]


def regCallbacks(tarId: str):

    @callback(
        [
            out({"type": k.tabVw, "taber": tarId, "id": ALL}, "className"),
            out({"type": k.tab, "taber": tarId, "id": ALL}, "className"),
            out({"type": k.tab, "taber": tarId, "id": ALL}, "children"),
        ],
        inp(id.store(tarId), "data"),
        ste({"type": k.tab, "taber": tarId, "id": ALL}, "children"),
        prevent_initial_call=True
    )
    def taber_onStoreChanged(dta_tab, chs_tab):

        if not dta_tab:
            lg.warn( "[taber:chg] no data" )
            return noUpd, noUpd

        tar = Taber.fromDict(dta_tab)

        css = tar.cssTabs()
        chs = tar.titles()

        # lg.info( f"[taber:chg] cssT: {css}" )
        # lg.info( f"[taber:chg] children: {chs}" )
        # lg.info( f"[taber:chg] children: {chs_tab}" )

        return css, css, chs

    #------------------------------------------------------------------------
    #
    #------------------------------------------------------------------------
    @callback(
        #[
            out(id.store(tarId), "data"),
            #out({"type": k.tab, "taber": tarId, "id": ALL}, "className"),
            #out(tarId, "children"),
        #],
        inp({"type": k.tab, "taber": tarId, "id": ALL}, "n_clicks"),
        [
            ste(id.store(tarId), "data"),
            # ste(tarId, "children"),
        ],
        prevent_initial_call=True
    )
    def taber_onClickTab(clks, dta_tab):
        if not dta_tab: return noUpd#, noUpd

        if not ctx.triggered or not ctx.triggered[0]["value"]:
            return noUpd#, noUpd

        #lg.info(f"[taber:click] data: {dta_tab}")
        taber = Taber.fromDict(dta_tab)

        # 找出被點擊的 tab
        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            tabId = ctx.triggered_id.get("id")

            # 檢查 tab 是否被禁用
            tab = taber.getTab(tabId)
            if tab and not tab.disabled:
                if tab.active and not tab.rehit:
                    lg.info(f"[taber] Ignoring click on already active tab: {tabId}")
                    return noUpd#, noUpd

                taber.setActive(tabId)
                lg.info(f"[taber] Tab clicked: {tabId}{' (refresh)' if tab.active else ''}")

        # 生成 className 列表
        css = []
        for tab in taber.tabs: css.append(tab.css())

        lg.info(f"[taber] clickTab[{tabId}]")

        # if not tItems:
        #     lg.warn( "[taber] =====>>> No Data?" )
        #     return taber.toDict(), []#, tItems
        #
        # if not isinstance(tItems, list):
        #     lg.warn( f"[taber] =====>>> Data not list? type({type(tItems)}): {tItems}" )
        #     return taber.toDict(), []#, tItems


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

        # dicHead = tItems[0]
        #
        # lg.info( f"head: {len(dicHead)}" )
        #
        # dicBody = tItems[1]
        #
        # lg.info( f"body: {len(dicBody)}" )

        return taber.toDict()#, taber.cssTabs()
