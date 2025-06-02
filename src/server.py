import os
import json
import requests
from flask import Flask, request, jsonify
from prometheus_client import Summary
from prometheus_flask_exporter import PrometheusMetrics


class Server(object):
    def __init__(self, endpoint_configurations, host='0.0.0.0', port=5000):
        self.host = host
        self.port = int(port)

        self.app = Flask(__name__)
        self._setup_metrics()

        # ✅ 處理 POST /
        @self.app.route("/", methods=["POST"])
        def webhook():
            try:
                data = request.get_json()
                print("✅ Received payload:", data)

                GAS_URL = "https://script.google.com/macros/s/AKfycbyk1pAzwGrkpRMtcTcmBaFftK5Egwfzj0lXILlr0lMCV-OXqAM_FO_SkEx-_9WTT9RA/exec?key=3b4b9657-4242-4a58-b24f-f2050a9fa7ea"
                headers = {"Content-Type": "application/json"}
                res = requests.post(GAS_URL, data=json.dumps(data), headers=headers, timeout=5)

                print(f"📤 Forwarded to GAS ({res.status_code}): {res.text}")
                return "OK", 200

            except Exception as e:
                print("❌ Error:", e)
                return jsonify({"error": str(e)}), 500

    def _setup_metrics(self):
        metrics = PrometheusMetrics(self.app)
        metrics.info('flask_app_info', 'App Info', version='1.0')

        Summary(
            'webhook_proxy_actions',
            'Action invocation metrics',
            labelnames=('http_route', 'http_method')
        )

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
