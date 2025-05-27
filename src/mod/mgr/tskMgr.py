import asyncio as aio
import json
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

import websockets as wss
from websockets.asyncio.server import ServerConnection

from util import log

lg = log.get(__name__)

DEBUG = False

class TskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TskInfo:
    id: str
    name: str
    status: TskStatus = TskStatus.PENDING
    prog: int = 0
    msg: str = ""
    result: Any = None
    err: Optional[str] = None
    dtc: float = field(default_factory=time.time)
    dts: Optional[float] = None
    dte: Optional[float] = None

class BseTsk(ABC):
    def __init__(self, tskId: str, name: str, hasCB: bool = True):
        self.tskId = tskId
        self.name = name
        self.hasCB = hasCB
        self._cancelled = False

    @abstractmethod
    def execute(self, callback: Optional[Callable[[int, str], None]] = None) -> Any:
        pass

    def cancel(self):
        self._cancelled = True

    @property
    def isCancelled(self) -> bool:
        return self._cancelled


#========================================================================
# Task Manager
#========================================================================
class TskMgr:
    def __init__(self, host: str = '0.0.0.0', port: int = 8765):
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
    async def _handler(self, conn: ServerConnection) -> None:
        self.conns.add(conn)

        cnt = len(self.conns)
        lg.info(f"[TskMgrWs] connected.. Total[{cnt}] conn[{id(conn)}]")

        try:
            await conn.send(json.dumps({
                'type': 'connected',
                'message': 'WebSocket connected to TskMgr'
            }))

            async for message in conn:
                if DEBUG: lg.info(f"[TskMgrWs] Received message from client: {message}")
                pass

        except wss.exceptions.ConnectionClosed as e:
            lg.info(f"[TskMgrWs] Connection closed: {e}")
        except Exception as e:
            lg.error(f"[TskMgrWs] HandleError: {e}")
        finally:
            if conn in self.conns:
                self.conns.remove(conn)
                lg.info(f"[TskMgrWs] disconnected.. Total[{len(self.conns)}] conn[{id(conn)}]")

    #------------------------------------------------
    # thread: ws
    #------------------------------------------------
    def _runSvcLoop(self):
        async def start_server():
            try:
                self.wsSvc = await wss.serve(self._handler, self.host, self.port)
                lg.info(f"[TskMgr] WebSocket server started on {self.host}:{self.port}")
            except OSError as e:
                lg.error(f"[TskMgr] WebSocket server error: {e}")
                raise

        self.wsLoop = aio.new_event_loop()
        aio.set_event_loop(self.wsLoop)

        self.wsLoop.run_until_complete(start_server())

        try:
            lg.info(f"[TskMgr] WebSocket event loop running")
            self.wsLoop.run_forever()
        except Exception as e:
            lg.error(f"[TskMgr] WebSocket event loop error: {e}")

    #================================================
    # open fn
    #================================================
    async def broadcast(self, message: dict):
        msgType = message.get('type')
        tskId = message.get('tskId')
        lg.info(f"[TskMgr:broadcast] START type[{msgType}] tskId[{tskId}] conns[{len(self.conns)}]")

        if self.conns:
            try:
                msg = json.dumps(message)
                if DEBUG: lg.info(f"[TskMgr:broadcast] JSON msg: {msg[:200]}...")
            except Exception as e:
                lg.error(f"[TskMgr:broadcast] JSON serialization failed: {e}")
                lg.error(f"[TskMgr:broadcast] Message type: {msgType}")
                lg.error(f"[TskMgr:broadcast] Message content: {message}")

                # Log specific field that might be problematic
                if 'result' in message:
                    lg.error(f"[TskMgr:broadcast] Result type: {type(message['result'])}")
                    if isinstance(message['result'], list):
                        for i, item in enumerate(message['result']):
                            lg.error(f"[TskMgr:broadcast] Result[{i}] type: {type(item)}, value: {item}")
                return

            disconnected = set()
            sentOk = 0
            for idx, c in enumerate(self.conns):
                try:
                    if DEBUG: lg.info(f"[TskMgr:broadcast] Sending to conn[{idx+1}/{len(self.conns)}]...")
                    await c.send(msg)
                    sentOk += 1

                    if message.get('type') == 'progress':
                        if DEBUG: lg.info(f"[TskMgr] Progress sent: {message.get('progress')}%")
                    elif message.get('type') == 'complete':
                        lg.info(f"[TskMgr] Complete sent: status[{message.get('status')}]")
                    elif message.get('type') == 'start':
                        lg.info(f"[TskMgr] Start sent: name[{message.get('name')}]")

                except Exception as e:
                    lg.error(f"[TskMgr] Broadcast error for conn[{idx+1}]: {e}")
                    disconnected.add(c)

            if DEBUG: lg.info(f"[TskMgr:broadcast] DONE sent[{sentOk}/{len(self.conns)}] disconnected[{len(disconnected)}]")
            self.conns -= disconnected

        elif message.get('type') in ['start', 'progress', 'complete']:
            lg.warning(f"[TskMgr] No clients for [{message.get('type')}] message")

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

            raise RuntimeError(f"[TskMgr] WebSocket event loop not ready after {tmMax}s")

    def stop(self):
        self.running = False
        for tskId in list(self.tsks.keys()):
            self.cancel(tskId)

    def regBy(self, task: BseTsk) -> str:
        task_info = TskInfo(id=task.tskId, name=task.name)
        self.infos[task.tskId] = task_info
        self.tsks[task.tskId] = task
        return task.tskId

    #------------------------------------------------
    # run on Thread
    #------------------------------------------------
    def _execute(self, tskId: str):
        task = self.tsks.get(tskId)
        info = self.infos.get(tskId)

        if not task or not info: return

        info.status = TskStatus.RUNNING
        info.dts = time.time()

        lastUpdate = 0
        def fnUpdater(progress: int, message: str):
            if task.hasCB:
                info.prog = progress
                info.msg = message
                
                nonlocal lastUpdate
                now = time.time()
                if now - lastUpdate < 1.0 and progress < 100:
                    return
                
                lastUpdate = now
                
                if self.wsLoop:
                    msg_data = {
                        'type': 'progress',
                        'tskId': tskId,
                        'progress': progress,
                        'message': message,
                        'status': info.status.value
                    }
                    # lg.info(f"[TskMgr] Sending progress: {msg_data}")
                    future = aio.run_coroutine_threadsafe(
                        self.broadcast(msg_data),
                        self.wsLoop
                    )
                    pass

        try:
            if self.wsLoop:
                start_msg = {
                    'type': 'start',
                    'tskId': tskId,
                    'name': info.name
                }
                # lg.info(f"[TskMgr] Sending start message: {start_msg}")
                aio.run_coroutine_threadsafe(
                    self.broadcast(start_msg),
                    self.wsLoop
                )

            result = task.execute(fnUpdater if task.hasCB else None)

            if task.isCancelled:
                info.status = TskStatus.CANCELLED
                info.msg = "Task cancelled"
            else:
                info.status = TskStatus.COMPLETED
                info.result = result
                info.prog = 100

        except Exception as e:
            info.status = TskStatus.FAILED
            info.err = str(e)
            info.msg = f"Error: {str(e)}"

        finally:
            info.dte = time.time()
            if self.wsLoop:
                complete_msg = {
                    'type': 'complete',
                    'tskId': tskId,
                    'status': info.status.value,
                    'result': info.result,
                    'error': info.err
                }
                if DEBUG: lg.info(f"[TskMgr] Sending complete message: {complete_msg}")
                aio.run_coroutine_threadsafe(
                    self.broadcast(complete_msg),
                    self.wsLoop
                )

            if tskId in self.threads: del self.threads[tskId]

    def run(self, tskId: str) -> bool:
        if tskId not in self.infos:
            lg.error(f"Task {tskId} not found in tasks")
            return False

        if tskId in self.threads:
            lg.warning(f"Task {tskId} already running")
            return False

        thread = threading.Thread(
            target=self._execute,
            args=(tskId,),
            daemon=True
        )
        self.threads[tskId] = thread
        thread.start()
        if DEBUG: lg.info(f"Task {tskId} thread started")
        return True

    def cancel(self, tskId: str) -> bool:
        task = self.tsks.get(tskId)
        if task:
            task.cancel()
            return True
        return False

    def getInfo(self, tskId: str) -> Optional[TskInfo]:
        return self.infos.get(tskId)

    def list(self) -> Dict[str, TskInfo]:
        return self.infos.copy()
