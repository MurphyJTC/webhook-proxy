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

        # ✅ 接受空的 endpoints（允許 webhook-only 模式）
        if endpoint_configurations is None:
            raise ConfigurationException('No endpoints defined')
        if isinstance(endpoint_configurations, list) and len(endpoint_configurations) == 0:
            print("⚠️ Warning: No endpoints configured, running in proxy-only mode.")

        Server.http_port = self.port

        if imports:
            for path in imports:
                import_action_module(path)

        Server.app = Flask(__name__)
        action_metrics = self._setup_metrics()

        # ✅ LINE Webhook Handler（POST /）
        @Server.app.route("/", methods=["POST"])
        def line_webhook():
            try:
                data = request.get_json()
                print("✅ Received LINE Webhook:", json.dumps(data, ensure_ascii=False))

                # ✅ Google Apps Script Webhook URL（請換成你自己的）
                GAS_URL = "https://script.google.com/macros/s/AKfycbyk1pAzwGrkpRMtcTcmBaFftK5Egwfzj0lXILlr0lMCV-OXqAM_FO_SkEx-_9WTT9RA/exec?key=3b4b9657-4242-4a58-b24f-f2050a9fa7ea"
                headers = {"Content-Type": "application/json"}

                # ✅ 設定 timeout，避免卡死
                res = requests.post(GAS_URL, data=json.dumps(data), headers=headers, timeout=5)

                print(f"📤 Forwarded to GAS ({res.status_code}): {res.text}")
                return "OK", 200

            except Exception as e:
                print("❌ Error in LINE webhook handler:", e)
                return jsonify({"error": str(e)}), 500

        # ✅ 加載 webhook-proxy endpoints（如有）
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
