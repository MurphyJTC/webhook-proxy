import signal
from server import Server

# 最小可執行版本
server = Server(endpoint_configurations=[], host="0.0.0.0", port=5000)

# graceful shutdown
signal.signal(signal.SIGTERM, lambda *args: exit(0))
signal.signal(signal.SIGINT, lambda *args: exit(0))

server.run()
