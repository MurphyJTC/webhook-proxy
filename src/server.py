import os
import json
import requests
from flask import Flask, request, jsonify
from prometheus_client import Summary
from prometheus_flask_exporter import PrometheusMetrics

from endpoints import Endpoint
from util import ConfigurationException, import_action_module


class Server(object):
    app = None
    http_port = None

    def __init__(self, endpoint_configurations, host='0.0.0.0', port=5000, imports=None):
        self.host = host
        self.port = int(port)

        if not endpoint_configurations:
            raise ConfigurationException('No endpoints defined')

        Server.http_port = self.port

        if imports:
            for path in imports:
                import_action_module(path)

        Server.app = Flask(__name__)
        action_metrics = self._setup_metrics()

        # ✅ 處理 LINE Webhook POST /
        @Server.app.route("/", methods=["POST"])
        def line_webhook():
            try:
                data = request.get_json()
                print("✅ Received LINE Webhook:", data)

                # ✅ 你的 Google Apps Script URL，請修改為你自己的
                GAS_URL = "https://script.google.com/macros/s/你的GAS-ID/exec?key=你的密鑰"
                headers = {"Content-Type": "application/json"}

                # ✅ 加入 timeout 限制，避免 LINE timeout
                res = requests.post(GAS_URL, data=json.dumps(data), headers=headers, timeout=5)

                print(f"📤 Forwarded to GAS ({res.status_code}): {res.text}")
                return "OK", 200

            except Exception as e:
                print("❌ Error in webhook handler:", e)
                return jsonify({"error": str(e)}), 500

        # 原本的 webhook-proxy endpoints 設定
        endpoints = [Endpoint(route, settings, action_metrics)
                     for config in endpoint_configurations
                     for route, settings in config.items()]

        for endpoint in endpoints:
            endpoint.setup(self.app)

    def _setup_metrics(self):
        metrics = PrometheusMetrics(self.app)

        metrics.info('flask_app_info', 'Application info',
                     version=os.environ.get('GIT_COMMIT') or 'unknown')

        metrics.info('flask_app_built_at', 'Application build timestamp').set(
            float(os.environ.get('BUILD_TIMESTAMP') or '0'))

        action_summary = Summary(
            'webhook_proxy_actions',
            'Action invocation metrics',
            labelnames=('http_route', 'http_method', 'action_type', 'action_index')
        )

        return action_summary

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
