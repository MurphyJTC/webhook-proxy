import signal
from server import Server

# ✅ 建立 Server（不需要讀設定檔）
server = Server(
    endpoint_configurations=[],  # 不啟用 YAML 的 endpoint 功能
    host='0.0.0.0',
    port=5000
)

# ✅ 處理 SIGTERM，讓 Vercel 關閉不會報錯
signal.signal(signal.SIGTERM, lambda *args: exit(0))
signal.signal(signal.SIGINT, lambda *args: exit(0))

# ✅ 啟動 Flask 應用（LINE webhook 會在 server.py 的 @app.route("/") 中處理）
server.run()
