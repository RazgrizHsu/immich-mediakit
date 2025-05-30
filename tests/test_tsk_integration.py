import time
import json
import asyncio
import websockets

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mod import models, mapFns, tskSvc

def test_fetch_assets(nfy, now, tsk, onUpdate):
    print(f"\n[Test] Starting task: {tsk.name}")

    for i in range(5):
        progress = (i + 1) * 20
        msg = f"Fetching assets... {progress}%"
        onUpdate(progress, f"{progress}%", msg)
        print(f"[Test] Progress: {progress}% - {msg}")
        time.sleep(0.5)

    nfy.success("Assets fetched successfully!")
    return nfy, now, "Completed fetching 100 assets"


async def test_websocket_client(port:int):
    uri = f"ws://localhost:{port}"
    messages = []

    async with websockets.connect(uri) as websocket:
        print("\n[WebSocket] Connected to server")

        nfy = models.Nfy()
        now = models.Now()
        tsk = models.Tsk()
        tsk.name = "Test Fetch Assets"
        tsk.cmd = "test.fetch"

        tskId = tskSvc.mkTask(
            name="Test Fetch Assets",
            cmd="test.fetch",
            fn=test_fetch_assets,
            nfy=nfy,
            now=now,
            tsk=tsk
        )

        print(f"[Test] Created task: {tskId}")

        await asyncio.sleep(0.5)

        success = tskSvc.runBy(tskId)
        print(f"[Test] Task started: {success}")

        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                messages.append(data)

                msg_type = data.get('type')
                print(f"\n[WebSocket] Received: {msg_type}")
                print(f"  Data: {json.dumps(data, indent=2)}")

                if msg_type == 'complete':
                    break

            except asyncio.TimeoutError:
                print("[WebSocket] Timeout waiting for message")
                break

    return messages


if __name__ == "__main__":

    port = 8087
    print(f"Testing UI Integration... port[{port}]")
    print("-" * 50)

    tskSvc.init(port, True)
    time.sleep(1)

    mapFns['test.fetch'] = test_fetch_assets

    try:
        messages = asyncio.run(test_websocket_client(port))

        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"Total messages received: {len(messages)}")

        msg_types = [msg.get('type') for msg in messages]
        print(f"Message types: {msg_types}")

        assert 'start' in msg_types, "Missing start message"
        assert 'progress' in msg_types, "Missing progress messages"
        assert 'complete' in msg_types, "Missing complete message"

        progress_msgs = [msg for msg in messages if msg.get('type') == 'progress']
        if progress_msgs:
            progress_values = [msg.get('progress', 0) for msg in progress_msgs]
            print(f"Progress values: {progress_values}")
            assert max(progress_values) >= 80, "Progress didn't reach expected value"

        complete_msg = next((msg for msg in messages if msg.get('type') == 'complete'), None)
        if complete_msg:
            assert complete_msg.get('status') == 'completed', f"Task status: {complete_msg.get('status')}"
            print(f"Result: {complete_msg.get('result')}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        tskSvc.stop()
        print("\n[Test] Task manager stopped")
