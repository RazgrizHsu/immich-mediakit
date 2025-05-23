import asyncio
import json
import time
import unittest
import uuid
from typing import Optional, Callable, Any
import websockets

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mod.mgr.tskMgr import TskMgr, BseTsk, TskStatus


def create_simple_task(name: str, duration: int = 5, hasCB: bool = True) -> BseTsk:
    class SimpleTask(BseTsk):
        def __init__(self):
            super().__init__(str(uuid.uuid4()), name, hasCB)
            self.duration = duration

        def execute(self, callback: Optional[Callable[[int, str], None]] = None) -> Any:
            steps = 10
            for i in range(steps):
                if self.isCancelled:
                    break

                progress = int((i + 1) / steps * 100)
                message = f"Processing step {i + 1}/{steps}"

                if callback:
                    callback(progress, message)

                time.sleep(self.duration / steps)

            return f"Task {self.name} completed!"

    return SimpleTask()


class TestTask(BseTsk):
    def __init__(self, tskId: str, name: str, steps: int = 5, hasCB: bool = True):
        super().__init__(tskId, name, hasCB)
        self.steps = steps
        self.executed = False
        self.final_progress = 0

    def execute(self, callback=None):
        self.executed = True
        for i in range(self.steps):
            if self.isCancelled:
                break

            progress = int((i + 1) / self.steps * 100)
            msg = f"Step {i + 1}/{self.steps}"
            self.final_progress = progress

            if callback:
                callback(progress, msg)

            time.sleep(0.1)

        return f"Completed {self.name}"

class TestTskMgr(unittest.TestCase):
    def setUp(self):
        self.manager = TskMgr(port=8766)
        self.manager.start()
        time.sleep(0.5)

    def tearDown(self):
        self.manager.stop()
        time.sleep(0.5)

    def test_register_task(self):
        task = TestTask("test1", "Test Task 1")
        tskId = self.manager.regBy(task)

        self.assertEqual(tskId, "test1")
        self.assertIn(tskId, self.manager.infos)
        self.assertEqual(self.manager.infos[tskId].name, "Test Task 1")
        self.assertEqual(self.manager.infos[tskId].status, TskStatus.PENDING)

    def test_start_task(self):
        task = TestTask("test2", "Test Task 2", steps=3)
        tskId = self.manager.regBy(task)

        success = self.manager.run(tskId)
        self.assertTrue(success)

        time.sleep(0.5)

        task_info = self.manager.getInfo(tskId)
        self.assertEqual(task_info.status, TskStatus.COMPLETED)
        self.assertEqual(task_info.prog, 100)
        self.assertTrue(task.executed)

    def test_task_with_callback(self):
        progress_updates = []

        class CallbackTask(BseTsk):
            def execute(self, callback=None):
                for i in range(5):
                    if callback:
                        progress = (i + 1) * 20
                        callback(progress, f"Progress {progress}%")
                        progress_updates.append(progress)
                    time.sleep(0.05)
                return "Done"

        task = CallbackTask("test3", "Callback Test")
        tskId = self.manager.regBy(task)
        self.manager.run(tskId)

        time.sleep(0.5)

        self.assertEqual(len(progress_updates), 5)
        self.assertEqual(progress_updates, [20, 40, 60, 80, 100])

    def test_task_without_callback(self):
        task = TestTask("test4", "No Callback Test", hasCB=False)
        tskId = self.manager.regBy(task)

        self.manager.run(tskId)
        time.sleep(0.6)

        task_info = self.manager.getInfo(tskId)
        self.assertEqual(task_info.status, TskStatus.COMPLETED)
        self.assertTrue(task.executed)

    def test_cancel_task(self):
        task = TestTask("test5", "Cancel Test", steps=10)
        tskId = self.manager.regBy(task)

        self.manager.run(tskId)
        time.sleep(0.2)

        success = self.manager.cancel(tskId)
        self.assertTrue(success)

        time.sleep(0.5)

        task_info = self.manager.getInfo(tskId)
        self.assertEqual(task_info.status, TskStatus.CANCELLED)
        self.assertTrue(task.final_progress < 100)

    def test_multiple_tasks(self):
        tasks = []
        for i in range(3):
            task = TestTask(f"multi{i}", f"Multi Task {i}", steps=3)
            tskId = self.manager.regBy(task)
            tasks.append(tskId)

        for tskId in tasks:
            self.manager.run(tskId)

        time.sleep(0.5)

        for tskId in tasks:
            task_info = self.manager.getInfo(tskId)
            self.assertEqual(task_info.status, TskStatus.COMPLETED)

    def test_task_error_handling(self):
        class ErrorTask(BseTsk):
            def execute(self, callback=None):
                if callback:
                    callback(50, "Half way")
                raise ValueError("Test error")

        task = ErrorTask("error1", "Error Test")
        tskId = self.manager.regBy(task)

        self.manager.run(tskId)
        time.sleep(0.5)

        task_info = self.manager.getInfo(tskId)
        self.assertEqual(task_info.status, TskStatus.FAILED)
        self.assertIsNotNone(task_info.err)
        self.assertIn("Test error", task_info.err)

    def test_create_simple_task(self):
        task = create_simple_task("Simple Test", duration=1)
        tskId = self.manager.regBy(task)

        self.manager.run(tskId)
        time.sleep(1.5)

        task_info = self.manager.getInfo(tskId)
        self.assertEqual(task_info.status, TskStatus.COMPLETED)
        self.assertEqual(task_info.result, "Task Simple Test completed!")

class TestWebSocketIntegration(unittest.TestCase):
    def setUp(self):
        self.manager = TskMgr(port=8767)
        self.manager.start()
        self.messages = []
        time.sleep(0.5)

    def tearDown(self):
        self.manager.stop()
        time.sleep(0.5)

    async def ws_client(self):
        uri = f"ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            task = TestTask("ws1", "WebSocket Test", steps=3)
            tskId = self.manager.regBy(task)
            self.manager.run(tskId)

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    self.messages.append(data)

                    if data.get('type') == 'complete':
                        break
                except asyncio.TimeoutError:
                    break

    def test_websocket_messages(self):
        asyncio.run(self.ws_client())

        self.assertTrue(len(self.messages) > 0)

        msg_types = [msg.get('type') for msg in self.messages]
        self.assertIn('start', msg_types)
        self.assertIn('progress', msg_types)
        self.assertIn('complete', msg_types)

        progress_msgs = [msg for msg in self.messages if msg.get('type') == 'progress']
        self.assertTrue(len(progress_msgs) >= 3)

        complete_msg = next(msg for msg in self.messages if msg.get('type') == 'complete')
        self.assertEqual(complete_msg.get('status'), TskStatus.COMPLETED.value)

if __name__ == '__main__':
    print("Running Task Manager Tests...")
    print("-" * 50)

    unittest.main(verbosity=2)
