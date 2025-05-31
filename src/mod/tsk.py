from typing import Tuple, Callable, Optional, List
import json, time, asyncio

from dsh import htm, dbc, inp, out, ste, callback, noUpd
from conf import ks
from util import log

from . import models
from .models import ITaskStore, IFnCall

# type define


# global function map
mapFns: dict[str, IFnCall] = {}

DEBUG = False

lg = log.get(__name__)

style_show = {'display': ''}
style_none = {'display': 'none'}

class k:
    wsId = 'global-task-ws'

    div = 'task-ws-div'
    prg = 'task-ws-progress'
    txt = 'task-ws-txt'
    rst = 'task-ws-result'
    btn = 'task-ws-btn-close'

def render():
    return htm.Div([
        dbc.Row([
            dbc.Col(htm.P("", id=k.txt), width=10),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Progress(id=k.prg, value=0, animated=True, striped=True, style={"height": "30px"}, label="0%")
            ], width=12, className="mb-2"),
        ]),

        dbc.Row([
            dbc.Col(htm.Div(id=k.rst), width=9),
            dbc.Col([
                dbc.Button("Test Ws", id="task-test-ws-btn", className="btn-success", size="sm", style=style_show if DEBUG else style_none),
                dbc.Button("close", id=k.btn, className="btn-info", size="sm", disabled=True),
            ], className="text-end"),
        ]),

        htm.Div(id="ws-state", style={'display': 'none'}),

    ],
        id=k.div,
        style=style_none, className="tskPanel"
    )


#========================================================================
# callbacks
#========================================================================
@callback(
    [
        out(k.div, "style"),
        out(k.txt, "children"),
    ],
    inp(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_PanelStatus(dta_tsk):
    tsk = models.Tsk.fromDict(dta_tsk)

    style = style_show if tsk.name else style_none

    # lg.info(f"[tsk:panel] id[{tsk.id}] name[{tsk.name}] tsk: {tsk}")

    return style, f"⌖ {tsk.name} ⌖"


@callback(
    out(ks.sto.tsk, "data", allow_duplicate=True),
    inp(k.btn, "n_clicks"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_onBtnClose(_nclk, dta_tsk):
    tsk = models.Tsk.fromDict(dta_tsk)
    if tsk.id or tsk.name:
        tsk.reset()
        lg.info("[tsk] close and reset..")
    return tsk.toDict()


@callback(
    out("ws-state", "children"),
    [
        inp(k.wsId, "state"),
        inp(k.wsId, "error")
    ],
    prevent_initial_call=True
)
def tsk_WsConnStatus(state, error):
    if error:
        lg.error(f"[tsk:ws] conn error: {error}")
        return f"ws error: {error}"
    if state:
        # lg.info(f"[tsk:ws] conn state changed: {state}")
        return f"conn state: {state}"

    return "ws connecting..."

@callback(
    out("ws-state", "children", allow_duplicate=True),
    inp(k.wsId, "message"),
    prevent_initial_call=True
)
def tsk_OnWsConnected(msg):
    if not msg: return noUpd
    try:
        data = json.loads(msg.get('data') if isinstance(msg, dict) else msg)
        if data.get('type') == 'connected':
            #lg.info(f"[tsk] connected msg[{data.get('message')}]")
            return "ws connected!"
    except Exception as e:
        lg.error(f"[tsk] Error handling connected message: {e}")
    return noUpd


@callback(
    [
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
    ],
    inp(ks.sto.tsk, "data"),
    ste(ks.sto.nfy, "data"),
    ste(ks.sto.now, "data"),
    ste(ks.sto.cnt, "data"),
    prevent_initial_call=True
)
def tsk_OnTasking(dta_tsk, dta_nfy, dta_now, dta_cnt):
    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)
    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)

    if not tsk.id or not tsk.cmd: return noUpd, noUpd

    #prevent task concurrent
    from .mgr.tskSvc import mgr
    if mgr:
        for tid, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                nfy.warn(f"Task already running, please wait for it to complete")
                return tsk.toDict(), nfy.toDict()

    from .mgr import tskSvc
    if DEBUG: lg.info(f"[tws:ing] Start.. id[{tsk.id}] name[{tsk.name}] cmd[{tsk.cmd}]")

    fn = mapFns.get(tsk.cmd)

    if not fn:
        msg = f"[tws:ing] mapFns cmd[{tsk.cmd}] not found"
        nfy.error(msg)
        return tsk.toDict(), nfy.toDict()

    try:
        sto = ITaskStore(nfy, now, cnt, tsk)

        tsn = tskSvc.mkTask(tsk, fn, sto)
        ok = tskSvc.runBy(tsn)
        tsk.tsn = tsn

        if ok:
            lg.info(f"[tws:ing] started, tsn[{tsn}] tsk: {tsk}")
            return tsk.toDict(), nfy.toDict()
        else:
            msg = "Failed to start task"
            nfy.error(msg)
            return tsk.toDict(), nfy.toDict()

    except Exception as e:
        msg = f"[tws:ing] Task failed: {str(e)}"
        lg.error(msg)
        nfy.error(msg)
        return tsk.toDict(), nfy.toDict()


@callback(
    [
        out(k.prg, "value"),
        out(k.prg, "label"),
        out(k.rst, "children"),
    ],
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    ste(k.rst, "children"),
    prevent_initial_call=True
)
def tsk_UpdUI(wmsg, dta_tsk, rstChs):
    if not wmsg: return noUpd, noUpd, noUpd

    # lg.info(f"[tws:uui] received: {wmsg}, tsk: {dta_tsk}")
    try:
        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        data = json.loads(rawData)
        tsk = models.Tsk.fromDict(dta_tsk)

        # 暫時不檢查 tsn，因為目前只支援單一任務
        # 之後可以改進為維護 tsn 映射表

        typ = data.get('type')

        if typ == 'start':
            if DEBUG: lg.info(f"[tws:uui] start: {data.get('name', '')}")
            return 0, "0%", f"Starting {data.get('name', '')}..."

        elif typ == 'progress':
            # lg.info(f"[tws:uui] prog recv: {data}")
            prog = data.get('progress', 0)
            msgs = data.get('message', '')

            if isinstance(msgs, list):
                htms = []
                for idx, line in enumerate(msgs):
                    if idx > 0: htms.append(htm.Br())
                    htms.append(line)

                lg.info(f"[tws:uui] prog[{prog}] htms[{htms}] ")
                return prog, f"{prog}%", htms
            else:
                lg.info(f"[tws:uui] prog[{prog}] msg[{msgs}] ")
                return prog, f"{prog}%", msgs

        elif typ == 'complete':
            ste = data.get('status')
            msg = data.get('message')

            if ste == 'failed':
                return 100, "Failed", msg if msg else "task failed"

            lg.info(f"[tws:uui] complete, ste[{ste}] chs[{rstChs}]")
            return 100, "completed", msg if msg else "⭐ completed"


    except Exception as e:
        lg.error(f"[tws:uui] Error parsing message: {e}")

    return noUpd, noUpd, noUpd


# 處理任務完成並更新 store
@callback(
    [
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.cnt, "data", allow_duplicate=True),
    ],
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_OnData(wmsg, dta_tsk):
    if not wmsg: return noUpd, noUpd, noUpd, noUpd

    try:
        # lg.info(f"[tws:dta] Called with msg: {wmsg}")

        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        data = json.loads(rawData)

        if data.get('type') == 'complete':
            lg.info(f"[tws:dta] Type[{data.get('type')}] tsn[{data.get('tsn')}]")
            tsk = models.Tsk.fromDict(dta_tsk)

            from .mgr import tskSvc
            sto = tskSvc.getResultBy(data.get('tsn'))

            dicNfy, dicNow, dicTsk, dicCnt = noUpd, noUpd, noUpd, noUpd

            if sto.nfy: dicNfy = sto.nfy.toDict()
            if sto.now: dicNow = sto.now.toDict()
            if sto.tsk:
                tsk = sto.tsk  #note: can't concurrent

                # 清除任務 ID 以允許執行新任務，但保留名稱供顯示
                tsk.id = None
                tsk.cmd = None

            dicCnt = models.Cnt.mkNewCnt().toDict()

            return dicNfy, dicNow, dicTsk, dicCnt
    except Exception as e:
        lg.error(f"[tws:dta] Error in tsk_OnComplete: {e}")

    return noUpd, noUpd, noUpd, noUpd


@callback(
    out(k.btn, "disabled"),
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_OnStatus(wmsg, dta_tsk):
    #lg.info(f"[tws:status] received:{wmsg}")

    if not wmsg: return noUpd

    try:
        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        data = json.loads(rawData)
        if DEBUG: lg.info(f"[tws:status] Type[{data.get('type')}] checking for complete...")
        tsk = models.Tsk.fromDict(dta_tsk)

        if data.get('type') == 'complete':
            if DEBUG: lg.info(f"[tws:status] Enabling close button for completed task")
            return False
    except Exception as e:
        lg.error(f"[tws:status] Error in OnStatusEnableBtnClose: {e}")

    return noUpd


# only for test
@callback(
    out("task-test-ws-btn", "disabled"),
    inp("task-test-ws-btn", "n_clicks"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_Test(n_clicks, dta_tsk):
    return noUpd
    # if DEBUG: lg.info(f"[TSW] Button clicked: {n_clicks}")
    #
    # from .mgr.tskSvc import mgr
    # if not n_clicks: return noUpd
    #
    # tsk = models.Tsk.fromDict(dta_tsk)
    # if DEBUG: lg.info(f"[TSW] Current task: id={tsk.id}, name={tsk.name}")
    #
    # if not tsk.id:
    #     lg.info("[TSW] Creating test task for ws test")
    #     tsk.id = f"ws-test-{n_clicks}"
    #     tsk.name = "ws Test"
    #
    # if not mgr:
    #     lg.error("[TSW] TskMgr not initialized")
    #     return noUpd
    #
    # if not mgr.wsLoop:
    #     lg.error("[TSW] TskMgr ws_loop not available")
    #     return noUpd
    #
    # lg.info(f"[TSW] TskMgr ready, sending progress messages for task: {tsk.id}")
    #
    # start_msg = {
    #     'type': 'start',
    #     'tsn': tsk.tsn,
    #     'name': 'ws Test'
    # }
    # asyncio.run_coroutine_threadsafe(
    #     mgr.broadcast(start_msg),
    #     mgr.wsLoop
    # )
    #
    # for i in range(5):
    #     progress = i * 20 + 20
    #     msg = {
    #         'type': 'progress',
    #         'tsn': tsk.tsn,
    #         'progress': progress,
    #         'message': f'Test progress {progress}%',
    #         'status': 'running'
    #     }
    #
    #     lg.info(f"[TSW] Sending progress: {progress}%")
    #
    #     asyncio.run_coroutine_threadsafe(
    #         mgr.broadcast(msg),
    #         mgr.wsLoop
    #     )
    #
    #     time.sleep(0.5)  # wait ui update
    #
    # complete_msg = {
    #     'type': 'complete',
    #     'tsn': tsk.tsn,
    #     'status': 'completed',
    #     'result': 'Test completed successfully',
    #     'error': None
    # }
    # asyncio.run_coroutine_threadsafe(
    #     mgr.broadcast(complete_msg),
    #     mgr.wsLoop
    # )
    # lg.info("[TSW] ws test completed")
    #
    # return noUpd
