import asyncio as aio
import json
import threading
import time
from datetime import datetime
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set

import websockets as wss
from websockets.asyncio.server import ServerConnection

from util import log

lg = log.get(__name__)

from mod.models import TskStatus, IFnRst, IFnProg

DEBUG = False


@dataclass
class TskInfo:
    sn: str
    name: str
    dtc: float
    status: TskStatus = TskStatus.PENDING
    prog: int = 0
    msg: str = ""
    result: Optional[IFnRst] = None
    err: Optional[str] = None
    dts: Optional[float] = None
    dte: Optional[float] = None


@dataclass
class BseTsk(ABC):
    name: str = field()

    @abstractmethod
    def run(self, doReport: Optional[IFnProg] = None) -> Any:
        pass


#========================================================================
# Task Manager
#========================================================================
class TskMgr:
    def __init__(self, host: str = '0.0.0.0', port: int = 8087):
        self.host = host
        self.port = port
        self.infos: Dict[str, TskInfo] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.tsks: Dict[str, BseTsk] = {}
        self.conns: Set[ServerConnection] = set()
        self.wsSvc = None
        self.thWsRecv = None
        self.running = False
        self.wsLoop = None

    #------------------------------------------------
    # thread: svc
    #------------------------------------------------
    async def _sendCurrentTaskStatus(self, conn: ServerConnection):
        """Send current running task status to newly connected client"""
        try:
            running_tasks = [(tsn, ti) for tsn, ti in self.infos.items() if ti.status in [TskStatus.RUNNING, TskStatus.PENDING]]

            if not running_tasks:
                # lg.info(f"[tskMgr] No running tasks to send to new client")
                return

            for tsn, ti in running_tasks:
                lg.info(f"[tskMgr] Sending current task status to new client: {ti.name} - {ti.status.value}")

                # Send start message
                start_msg = {
                    'type': 'start',
                    'tsn': tsn,
                    'name': ti.name
                }
                lg.info(f"[tskMgr] Sending start message: {start_msg}")
                await conn.send(json.dumps(start_msg))

                # Send current progress if running
                if ti.status == TskStatus.RUNNING:
                    progress_msg = {
                        'type': 'progress',
                        'tsn': tsn,
                        'progress': ti.prog,
                        'message': ti.msg,
                        'status': ti.status.value
                    }
                    lg.info(f"[tskMgr] Sending progress message: {progress_msg}")
                    await conn.send(json.dumps(progress_msg))

                break  # Only one task should be running at a time
        except Exception as e:
            lg.error(f"[tskMgr] Error sending current task status: {e}")

    #------------------------------------------------
    async def _handler(self, conn: ServerConnection) -> None:
        self.conns.add(conn)

        cnt = len(self.conns)
        lg.info(f"[tskMgr] connected.. Total[{cnt}] conn[{id(conn)}]")

        try:
            await conn.send(json.dumps({
                'type': 'connected',
                'message': 'WebSocket connected to TskMgr'
            }))

            # Small delay to ensure client is ready
            import asyncio
            await asyncio.sleep(0.1)

            # Send current running task status to newly connected client
            await self._sendCurrentTaskStatus(conn)

            async for message in conn:
                if DEBUG: lg.info(f"[tskMgr] Received message from client: {message}")
                pass

        except wss.exceptions.ConnectionClosed as e:
            lg.info(f"[tskMgr] Connection closed: {e}")
        except Exception as e:
            lg.error(f"[tskMgr] HandleError: {e}")
        finally:
            if conn in self.conns:
                self.conns.remove(conn)
                lg.info(f"[tskMgr] disconnected.. Total[{len(self.conns)}] conn[{id(conn)}]")

    #------------------------------------------------
    # thread: ws
    #------------------------------------------------
    def _runSvcLoop(self):
        async def start_server():
            try:
                self.wsSvc = await wss.serve(self._handler, self.host, self.port)
                lg.info(f"[tskMgr] WebSocket server started on {self.host}:{self.port}")
            except OSError as e:
                lg.error(f"[tskMgr] WebSocket server error: {e}")
                raise

        self.wsLoop = aio.new_event_loop()
        aio.set_event_loop(self.wsLoop)

        self.wsLoop.run_until_complete(start_server())

        try:
            lg.info(f"[tskMgr] WebSocket event loop running")
            self.wsLoop.run_forever()
        except Exception as e:
            lg.error(f"[tskMgr] WebSocket event loop error: {e}")

    #================================================
    # open fn
    #================================================
    async def broadcast(self, wmsg: dict):
        msgType = wmsg.get('type')
        tsn = wmsg.get('tsn')
        # lg.info(f"[tskMgr:broadcast] START type[{msgType}] tsn[{tsn}] conns[{len(self.conns)}]")

        if self.conns:
            try:
                msgStr = json.dumps(wmsg)
                if DEBUG: lg.info(f"[tskMgr:broadcast] JSON msg: {msgStr[:200]}...")
            except Exception as e:
                lg.error(f"[tskMgr:broadcast] JSON serialization failed: {e}")
                lg.error(f"[tskMgr:broadcast] Message type: {msgType}")
                lg.error(f"[tskMgr:broadcast] Message content: {wmsg}")
                return

            disconnected = set()
            sentOk = 0
            for idx, c in enumerate(self.conns):
                try:
                    if DEBUG: lg.info(f"[tskMgr:broadcast] Sending to conn[{idx + 1}/{len(self.conns)}]...")
                    await c.send(msgStr)
                    sentOk += 1

                    if wmsg.get('type') == 'progress':
                        if DEBUG: lg.info(f"[tskMgr] Progress sent: {wmsg.get('progress')}%")
                    elif wmsg.get('type') == 'complete':
                        lg.info(f"[tskMgr] Complete sent: status[{wmsg.get('status')}]")
                    elif wmsg.get('type') == 'start':
                        lg.info(f"[tskMgr] Start sent: name[{wmsg.get('name')}]")

                except Exception as e:
                    lg.error(f"[tskMgr] Broadcast error for conn[{idx + 1}]: {e}")
                    disconnected.add(c)

            if DEBUG: lg.info(f"[tskMgr:broadcast] DONE sent[{sentOk}/{len(self.conns)}] disconnected[{len(disconnected)}]")
            self.conns -= disconnected

        elif wmsg.get('type') in ['start', 'progress', 'complete']:
            lg.warning(f"[tskMgr] No clients for [{wmsg.get('type')}] message")

    def start(self):
        if not self.running:
            self.running = True
            self.thWsRecv = threading.Thread(target=self._runSvcLoop, daemon=True)
            self.thWsRecv.start()

            tmMax = 5
            tmUse = 0
            while not self.wsLoop and tmUse < tmMax:
                time.sleep(0.1)
                tmUse += 0.1
            if self.wsLoop: return

            raise RuntimeError(f"[tskMgr] WebSocket event loop not ready after {tmMax}s")

    def stop(self):
        self.running = False

    def regBy(self, task: BseTsk) -> str:
        dt = datetime.now()
        sn = str(uuid.uuid4())

        ti = TskInfo(sn=sn, name=task.name, dtc=dt.timestamp())

        self.infos[sn] = ti
        self.tsks[sn] = task
        return sn

    def cancel(self, tsn: str) -> bool:
        if tsn not in self.infos: return False

        ti = self.infos[tsn]
        if ti.status in [TskStatus.COMPLETED, TskStatus.FAILED, TskStatus.CANCELLED]: return False

        ti.status = TskStatus.CANCELLED
        ti.dte = time.time()

        lg.info(f"[tskMgr] Task {tsn} cancelled, sending complete message")

        # Send cancel complete message to update UI
        import asyncio
        if self.wsLoop:
            def sendCancelMessage():
                asyncio.run_coroutine_threadsafe(
                    self.broadcast({
                        'type': 'complete',
                        'tsn': tsn,
                        'message': ti.msg,
                        'status': ti.status.value,
                        'error': None
                    }),
                    self.wsLoop #type:ignore
                )
            sendCancelMessage()

        return True

    def isCancelled(self, tsn: str) -> bool:
        if tsn not in self.infos: return False
        return self.infos[tsn].status == TskStatus.CANCELLED

    #------------------------------------------------
    # run on Thread
    #------------------------------------------------
    def _execOnThread(self, tsn: str):
        tk = self.tsks.get(tsn)
        ti = self.infos.get(tsn)

        if not tk or not ti: return

        ti.status = TskStatus.RUNNING
        ti.dts = time.time()

        #------------------------------------
        # sending
        #------------------------------------
        def doSend(msg):
            # lg.info(f"[tskMgr] send: {msg}")
            future = aio.run_coroutine_threadsafe(
                self.broadcast(msg),
                self.wsLoop #type:ignore
            )
            pass

        #------------------------------------
        dtu = 0

        def fnReport(pct: int, msg: str):
            if ti.status == TskStatus.CANCELLED: return  # Stop reporting if cancelled

            ti.prog = pct
            ti.msg = msg

            nonlocal dtu
            now = time.time()
            if now - dtu < 0.3 and pct < 100: return #limit sec
            dtu = now

            doSend({
                'type': 'progress',
                'tsn': tsn,
                'progress': pct,
                'message': msg,
                'status': ti.status.value
            })
            pass

        #------------------------------------
        try:
            doSend({
                'type': 'start',
                'tsn': tsn,
                'name': ti.name
            })

            if ti.status != TskStatus.CANCELLED:
                sto, retMsg = tk.run(fnReport)

                if ti.status == TskStatus.CANCELLED:
                    ti.msg = "Task was cancelled"
                    ti.prog = 0
                else:
                    ti.status = TskStatus.COMPLETED
                    ti.result = sto
                    ti.prog = 100
                    ti.msg = retMsg

        except Exception as e:
            if ti.status == TskStatus.CANCELLED:
                ti.msg = "Task was cancelled"
            else:
                ti.status = TskStatus.FAILED
                ti.err = str(e)
                ti.msg = f"Error: {str(e)}"

        finally:
            ti.dte = time.time()

            # Only send complete message if not already sent by cancel()
            if ti.status != TskStatus.CANCELLED:
                doSend( {
                    'type': 'complete',
                    'tsn': tsn,
                    'message': ti.msg,
                    'status': ti.status.value,
                    'error': ti.err
                })

            if tsn in self.threads: del self.threads[tsn]

    def run(self, tsn: str) -> bool:
        if tsn not in self.infos:
            raise RuntimeError(f"Task {tsn} not found in tasks")

        if tsn in self.threads:
            raise RuntimeError(f"Task {tsn} already running")

        thread = threading.Thread(
            target=self._execOnThread,
            args=(tsn,),
            daemon=True
        )
        self.threads[tsn] = thread
        thread.start()
        # if DEBUG: lg.info(f"Task {tsn} thread started")
        return True


    def getInfo(self, tsn: str) -> Optional[TskInfo]:
        return self.infos.get(tsn)

    def list(self) -> Dict[str, TskInfo]:
        return self.infos.copy()


    def hasRunning(self):
        for tid, info in self.list().items():
            if info.status.value in ['pending', 'running']:
                return True

        return False
