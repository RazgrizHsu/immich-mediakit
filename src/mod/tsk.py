from typing import Tuple, Callable, Optional, List
import json, time, asyncio

from dsh import htm, dbc, inp, out, ste, cbk, noUpd
from conf import ks
from util import log

from . import models
from .models import ITaskStore, IFnCall
import db
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
    btnFloat = 'task-float-btn'
    btnCancel = 'task-ws-btn-cancel'

def render():
    return htm.Div([
        dbc.Row([
            dbc.Col(htm.P("", id=k.txt), width=6),
            dbc.Col([
                dbc.Button("Float", id=k.btnFloat, className="btn-primary btn-sm txt-sm", size="sm"),
                dbc.Button("❎", id=k.btn, className="btn-outline-secondary btn-sm ms-2", size="sm", disabled=True),
            ], className="text-end"),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Progress(id=k.prg, value=0, animated=True, striped=True, style={"height": "30px"}, label="0%")
            ], width=12, className="mb-2"),
        ]),

        dbc.Row([
            dbc.Col(htm.Div(id=k.rst), width=8),
            dbc.Col([
                dbc.Button("Test Ws", id="task-test-ws-btn", className="btn-success", size="sm", style=style_show if DEBUG else style_none),
                dbc.Button("Cancel", id=k.btnCancel, className="btn-warning", size="sm", disabled=True),
            ], className="text-end"),
        ]),

        htm.Div(id="ws-state", style={'display': 'none'}),

    ],
        id=k.div,
        style=style_none, className=f"tskPanel {'fly' if db.dto.tskFloat else ''}"
    )


#========================================================================
# callbacks
#========================================================================
@cbk(
    [
        out(k.div, "style"),
        out(k.txt, "children"),
        out(k.btnCancel, "disabled", allow_duplicate=True),
        out(k.btn, "disabled", allow_duplicate=True),
    ],
    inp(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_PanelStatus(dta_tsk):
    tsk = models.Tsk.fromDict(dta_tsk)

    style = style_show if tsk.name else style_none

    # Enable cancel button if task is running, close button only when task completed
    cancelDisabled = not (tsk.id and tsk.name)
    closeDisabled = (tsk.id and tsk.name)  # Disable close when task is running

    # lg.info(f"[tsk:panel] id[{tsk.id}] name[{tsk.name}] cancel_disabled[{cancelDisabled}] close_disabled[{closeDisabled}]")

    return style, f"⌖ {tsk.name} ⌖", cancelDisabled, closeDisabled


@cbk(
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

@cbk(
    [
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(k.btnCancel, "disabled", allow_duplicate=True),
    ],
    inp(k.btnCancel, "n_clicks"),
    ste(ks.sto.tsk, "data"),
    ste(ks.sto.nfy, "data"),
    prevent_initial_call=True
)
def tsk_onBtnCancel(_nclk, dta_tsk, dta_nfy):
    if not _nclk: return noUpd.by(2)

    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)

    lg.info(f"[tsk] Cancel button clicked, tsk.id[{tsk.id}] tsk.tsn[{tsk.tsn}]")

    if not tsk.tsn:
        nfy.warn("No running task to cancel")
        return nfy.toDict(), noUpd

    from .mgr import tskSvc

    if tskSvc.cancelBy(tsk.tsn):
        nfy.info(f"Task {tsk.name} cancelled")
        lg.info(f"[tsk] Cancelled task: {tsk.tsn}")
        return nfy.toDict(), True  # Disable cancel button
    else:
        nfy.warn("Failed to cancel task")
        return nfy.toDict(), noUpd


@cbk(
    out(k.div, "className"),
    inp(k.btnFloat, "n_clicks"),
    ste(k.div, "className"),
    prevent_initial_call=True
)
def tsk_onBtnFloat(_nclk, curCls):
    db.dto.tskFloat = not db.dto.tskFloat
    return "tskPanel fly" if db.dto.tskFloat else "tskPanel"


@cbk(
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

@cbk(
    out("ws-state", "children", allow_duplicate=True),
    inp(k.wsId, "message"),
    prevent_initial_call=True
)
def tsk_OnWsConnected(msg):
    if not msg: return noUpd
    try:
        rawData = msg.get('data') if isinstance(msg, dict) else msg
        if not rawData: raise RuntimeError( "[wsid] not rawData" )

        data = json.loads(rawData)
        if data.get('type') == 'connected':
            #lg.info(f"[tsk] connected msg[{data.get('message')}]")
            return "ws connected!"
    except Exception as e:
        lg.error(f"[tsk] Error handling connected message: {e}")
    return noUpd


@cbk(
    [
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
    ],
    inp(ks.sto.tsk, "data"),
    ste(ks.sto.nfy, "data"),
    ste(ks.sto.now, "data"),
    ste(ks.sto.cnt, "data"),
    ste(ks.sto.ste, "data"),
    prevent_initial_call=True
)
def tsk_OnTasking(dta_tsk, dta_nfy, dta_now, dta_cnt, dta_ste):
    tsk = models.Tsk.fromDict(dta_tsk)
    nfy = models.Nfy.fromDict(dta_nfy)
    now = models.Now.fromDict(dta_now)
    cnt = models.Cnt.fromDict(dta_cnt)
    ste = models.Ste.fromDict(dta_ste)

    if not tsk.id or not tsk.cmd: return noUpd.by(2)

    #prevent task concurrent
    from .mgr.tskSvc import mgr
    if mgr:
        for tid, info in mgr.list().items():
            if info.status.value in ['pending', 'running']:
                nfy.warn(f"Task already running, please wait for it to complete")
                return tsk.toDict(), nfy.toDict()

    from .mgr import tskSvc

    lg.info(f"[tws:ing] into id[{tsk.id}] name[{tsk.name}] cmd[{tsk.cmd}]")

    fn = mapFns.get(tsk.cmd)

    if not fn:
        msg = f"[tws:ing] mapFns cmd[{tsk.cmd}] not found"
        nfy.error(msg)
        return tsk.toDict(), nfy.toDict()

    try:
        sto = ITaskStore(nfy, now, cnt, tsk, ste)

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


@cbk(
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
    if not wmsg: return noUpd.by(3)

    # lg.info(f"[tws:uui] received: {wmsg}, tsk: {dta_tsk}")
    try:
        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        if not rawData: raise RuntimeError( "[tsk] no rawData" )
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

            if isinstance(msg, list):
                htms = []
                for idx, line in enumerate(msg):
                    if idx > 0: htms.append(htm.Br())
                    htms.append(line)
                msg = htms

            if ste == 'failed':
                return 100, "Failed", msg if msg else "task failed"

            if ste == 'cancelled':
                return 100, "Cancelled", msg if msg else "task cancelled"

            lg.info(f"[tws:uui] complete, ste[{ste}] chs[{rstChs}]")
            return 100, "completed", msg if msg else "⭐ completed"


    except Exception as e:
        lg.error(f"[tws:uui] Error parsing message: {e}")

    return noUpd.by(3)


# 處理任務完成並更新 store
@cbk(
    [
        out(ks.sto.cnt, "data", allow_duplicate=True),
        out(ks.sto.nfy, "data", allow_duplicate=True),
        out(ks.sto.now, "data", allow_duplicate=True),
        out(ks.sto.tsk, "data", allow_duplicate=True),
        out(ks.sto.ste, "data", allow_duplicate=True),
    ],
    inp(k.wsId, "message"),
    prevent_initial_call=True
)
def tsk_OnData(wmsg):
    if not wmsg: return noUpd.by(5)

    try:
        # lg.info(f"[tws:dta] Called with msg: {wmsg}")

        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        if not rawData: raise RuntimeError( "[tsk] no rawData" )
        data = json.loads(rawData)

        if data.get('type') == 'complete':
            lg.info(f"[tws:dta] Type[{data.get('type')}] tsn[{data.get('tsn')}]")

            from .mgr import tskSvc
            sto = tskSvc.getResultBy(data.get('tsn'))

            dicCnt, dicNfy, dicNow, dicTsk, dicSte = noUpd.by(5)

            # every task refresh cnt
            dicCnt = models.Cnt.mkNewCnt().toDict()

            dicNfy = sto.nfy.toDict()
            dicNow = sto.now.toDict()
            dicSte = sto.ste.toDict()

            tsk = sto.tsk  #note: can't concurrent

            if tsk.nexts and len(tsk.nexts):
                ntsk = tsk.nexts[0]
                ntsk.nexts = tsk.nexts[1:]

                dicTsk = ntsk.toDict()
            else:
                # clear id & cmd but keep name
                # name only display, but id & cmd will trigger new task
                tsk.id = None
                tsk.cmd = None
                dicTsk = tsk.toDict()

            return dicCnt, dicNfy, dicNow, dicTsk, dicSte

    except Exception as e:
        lg.error(f"[tws:dta] Error in tsk_OnComplete: {e}", exc_info=True)

    return noUpd.by(5)


@cbk(
    [
        out(k.btn, "disabled"),
        out(k.btnCancel, "disabled"),
    ],
    inp(k.wsId, "message"),
    ste(ks.sto.tsk, "data"),
    prevent_initial_call=True
)
def tsk_OnStatus(wmsg, dta_tsk):
    if not wmsg: return noUpd.by(2)

    try:
        rawData = wmsg.get('data') if isinstance(wmsg, dict) else wmsg
        if not rawData: raise RuntimeError( "[tsk] no rawData" )
        data = json.loads(rawData)
        msgType = data.get('type')
        tsk = models.Tsk.fromDict(dta_tsk)

        if msgType == 'start':
            return True, False  # Disable close, enable cancel
        elif msgType == 'complete':
            return False, True  # Enable close, disable cancel
    except Exception as e:
        lg.error(f"[tws:status] Error in OnStatusEnableBtnClose: {e}")

    return noUpd.by(2)


# only for test
# @cbk(
#     out("task-test-ws-btn", "disabled"),
#     inp("task-test-ws-btn", "n_clicks"),
#     ste(ks.sto.tsk, "data"),
#     prevent_initial_call=True
# )
# def tsk_Test(n_clicks, dta_tsk):
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
