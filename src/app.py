import signal
from server import Server

# ✅ 最小設定：允許空 endpoints
server = Server(endpoint_configurations=[], host="0.0.0.0", port=5000)

# ✅ 終止訊號處理
signal.signal(signal.SIGTERM, lambda *args: exit(0))
signal.signal(signal.SIGINT, lambda *args: exit(0))

# ✅ 啟動 Flask app
server.run()
