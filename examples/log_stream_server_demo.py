"""启动日志流服务并持续生成演示事件。

最小客户端示例::

    async with websockets.connect("ws://127.0.0.1:8765") as websocket:
        message = await websocket.recv()
        print(message)
"""

from __future__ import annotations

import tempfile
import time

from casevo.util.log_stream_server import LogStreamServer
from casevo.util.tot_log_stream import TotLogStream


def main() -> None:
    """启动服务，每秒交替发布模型和代理日志，直到用户中断。"""
    server = LogStreamServer()
    with tempfile.TemporaryDirectory(prefix="casevo-log-stream-") as log_dir:
        TotLogStream.init_log(1, log_dir, buffer_size=10_000)
        server.start()
        print(f"LogStreamServer listening on ws://{server.host}:{server.port}")
        print("Connect a WebSocket client to receive events. Press Ctrl+C to stop.")

        index = 0
        try:
            while True:
                if index % 2 == 0:
                    TotLogStream.add_model_log(index, "thought", {"index": index})
                else:
                    TotLogStream.add_agent_log(
                        index, "action", {"index": index}, tar_agent_id=0
                    )
                index += 1
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping LogStreamServer...")
        finally:
            server.stop()


if __name__ == "__main__":
    main()

