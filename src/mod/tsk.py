from typing import Tuple, Callable
import json, time, asyncio

from dsh import htm, dbc, inp, out, ste, callback, noUpd
from conf import ks
from util import log
from . import models

# type define
IFnProg = Callable[[int, str, str], None]
IFnCall = Callable[[
    models.Nfy,
    models.Now,
    models.Tsk,
    IFnProg
], Tuple[models.Nfy, models.Now, str]]

# global function map
mapFns: dict[str, IFnCall] = {}

DEBUG_WS = False

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
            dbc.Col(htm.Div(id=k.rst), width=6),
            dbc.Col([
                dbc.Button("Test Ws", id="task-test-ws-btn", className="btn-success", size="sm", style=style_show if DEBUG_WS else style_none),
                dbc.Button("close to continue", id=k.btn, className="btn-info", size="sm", disabled=True),
            ], className="text-end"),
        ]),

        htm.Div(id="ws-state", style={'display': 'none'}),

    ],
        id=k.div,
        style=style_none, className="tskPanel"
    )




# panel display
@callback(
    [
        out(k.div, "style"),
        out(k.txt, "children"),
    ],
    inp(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_PanelStatus(dta_tsk):
    tsk = models.Tsk.fromStore(dta_tsk)
    hasTsk = tsk.name is not None
    style = style_show if hasTsk else style_none

    lg.info(f"[TaskWS] Update display: {hasTsk} id[{tsk.id}] name[{tsk.name}]")
    return style, tsk.name


@callback(
    out(ks.sto.tsk, "data"),
    inp(k.btn, "n_clicks"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_onBtnClose(_nclk, dta_tsk):
    tsk = models.Tsk.fromStore(dta_tsk)
    if tsk.id or tsk.name:
        tsk.reset()
        lg.info("[TaskWS] close and reset..")
    return tsk.toStore()



#========================================================================
# handle wsId
#========================================================================

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
        lg.error(f"[TaskWS] WebSocket error: {error}")
        return f"WebSocket error: {error}"
    if state:
        lg.info(f"[TaskWS] WebSocket state changed: {state}")
        return f"WebSocket state: {state}"
    return "WebSocket connecting..."

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
            lg.info(f"[TaskWS] Received connected message: {data.get('message')}")
            return "WebSocket connected!"
    except Exception as e:
        lg.error(f"[TaskWS] Error handling connected message: {e}")
    return noUpd

@callback(
    [
        out(k.prg, "value"),
        out(k.prg, "label"),
        out(k.rst, "children"),
    ],
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_OnTskUpdate(msg, dta_tsk):
    if DEBUG_WS: lg.info(f"[TaskWS] WebSocket message received in ws_update_progress: {msg}")
    if not msg: return noUpd, noUpd, noUpd

    try:
        data = json.loads(msg.get('data') if isinstance(msg, dict) else msg)
        tsk = models.Tsk.fromStore(dta_tsk)

        # 暫時不檢查 tskId，因為目前只支援單一任務
        # 之後可以改進為維護 tskId 映射表

        typ = data.get('type')

        if typ == 'progress':
            progress = data.get('progress', 0)
            message = data.get('message', '')
            return progress, f"{progress}%", message

        elif typ == 'complete':
            ste = data.get('status')
            lg.info(f"[TaskWS] Task completed with status: {ste}")
            if ste == 'completed':
                return 100, "100%", data.get('result', 'Task completed')
            elif ste == 'failed':
                return 100, "Failed", data.get('error', 'Task failed')
            elif ste == 'cancelled':
                return data.get('progress', 0), "Cancelled", "Task cancelled"

        elif typ == 'start':
            lg.info(f"[TaskWS] Task starting: {data.get('name', 'task')}")
            return 0, "0%", f"Starting {data.get('name', 'task')}..."

    except Exception as e:
        lg.error(f"[TaskWS-Progress] Error parsing message: {e}")

    return noUpd, noUpd, noUpd


@callback(
    [
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
    ],
    inp(ks.sto.tsk, "data"),
    ste(ks.sto.nfy, "data"),
    ste(ks.sto.now, "data"),
    prevent_initial_call=True
)
def tsk_OnTasking(dta_tsk, dta_nfy, dta_now):
    tsk = models.Tsk.fromStore(dta_tsk)
    nfy = models.Nfy.fromStore(dta_nfy)
    now = models.Now.fromStore(dta_now)

    if not tsk.id or not tsk.cmd: return noUpd, noUpd, noUpd

    from .mgr import tskSvc
    lg.info(f"[TaskWS] Start.. id[{tsk.id}] name[{tsk.name}] cmd[{tsk.cmd}]")

    fn = mapFns.get(tsk.cmd)

    if not fn:
        msg = f"[TaskWS] mapFns cmd[{tsk.cmd}] not found"
        nfy.error(msg)
        return tsk.toStore(), nfy.toStore(), now.toStore()

    try:
        tskId = tskSvc.mkTask(tsk.name, tsk.cmd, fn, nfy, now, tsk)
        tsk.id = tskId  # 更新 task ID
        ok = tskSvc.runBy(tskId)

        if ok:
            lg.info(f"[TaskWS] Task started successfully: {tskId}")
            return tsk.toStore(), nfy.toStore(), now.toStore()
        else:
            msg = "Failed to start task"
            nfy.error(msg)
            return tsk.toStore(), nfy.toStore(), now.toStore()

    except Exception as e:
        msg = f"Task execution failed: {str(e)}"
        lg.error(msg)
        nfy.error(msg)
        return tsk.toStore(), nfy.toStore(), now.toStore()


# 處理任務完成並更新 store
@callback(
    [
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
    ],
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_OnComplete(msg, dta_tsk):
    if not msg: return noUpd, noUpd, noUpd

    try:
        data = json.loads(msg.get('data') if isinstance(msg, dict) else msg)
        tsk = models.Tsk.fromStore(dta_tsk)

        if data.get('type') == 'complete':
            from .mgr.tskSvc import getResultBy
            nfy, now, result = getResultBy(data.get('tskId'))

            if nfy and now:
                lg.info(f"[TaskWS] Task completed, updating stores with results")
                # 清除任務 ID 以允許執行新任務，但保留名稱供顯示
                tsk.id = None
                tsk.cmd = None
                return nfy.toStore(), now.toStore(), tsk.toStore()
    except Exception as e:
        lg.error(f"[TaskWS] Error in handle_task_complete: {e}")

    return noUpd, noUpd, noUpd


@callback(
    out(k.btn, "disabled"),
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def enable_close_on_complete(msg, dta_tsk):
    if DEBUG_WS: lg.info(f"[TaskWS] WebSocket message received in enable_close_on_complete: {msg}")

    if not msg: return noUpd

    try:
        data = json.loads(msg.get('data') if isinstance(msg, dict) else msg)
        tsk = models.Tsk.fromStore(dta_tsk)

        if data.get('type') == 'complete':
            if DEBUG_WS: lg.info(f"[TaskWS] Enabling close button for completed task")
            return False
    except Exception as e:
        lg.error(f"[TaskWS] Error in enable_close_on_complete: {e}")

    return noUpd










# only for test
@callback(
    out("task-test-ws-btn", "disabled"),
    inp("task-test-ws-btn", "n_clicks"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_Test(n_clicks, dta_tsk):
    lg.info(f"[Test-WS] Button clicked: {n_clicks}")

    from .mgr.tskSvc import mgr
    if not n_clicks:
        return noUpd

    tsk = models.Tsk.fromStore(dta_tsk)
    lg.info(f"[Test-WS] Current task: id={tsk.id}, name={tsk.name}")

    if not tsk.id:
        lg.info("[Test-WS] Creating test task for WebSocket test")
        tsk.id = f"ws-test-{n_clicks}"
        tsk.name = "WebSocket Test"

    if not mgr:
        lg.error("[Test-WS] TskMgr not initialized")
        return noUpd

    if not mgr.wsLoop:
        lg.error("[Test-WS] TskMgr ws_loop not available")
        return noUpd

    lg.info(f"[Test-WS] TskMgr ready, sending progress messages for task: {tsk.id}")

    start_msg = {
        'type': 'start',
        'tskId': tsk.id,
        'name': 'WebSocket Test'
    }
    asyncio.run_coroutine_threadsafe(
        mgr.broadcast(start_msg),
        mgr.wsLoop
    )

    for i in range(5):
        progress = i * 20 + 20
        msg = {
            'type': 'progress',
            'tskId': tsk.id,
            'progress': progress,
            'message': f'Test progress {progress}%',
            'status': 'running'
        }

        lg.info(f"[Test-WS] Sending progress: {progress}%")

        asyncio.run_coroutine_threadsafe(
            mgr.broadcast(msg),
            mgr.wsLoop
        )

        time.sleep(0.5) # wait ui update


    complete_msg = {
        'type': 'complete',
        'tskId': tsk.id,
        'status': 'completed',
        'result': 'Test completed successfully',
        'error': None
    }
    asyncio.run_coroutine_threadsafe(
        mgr.broadcast(complete_msg),
        mgr.wsLoop
    )
    lg.info("[Test-WS] WebSocket test completed")

    return noUpd
