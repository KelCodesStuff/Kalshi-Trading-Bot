import time
from prometheus_client import start_http_server, Gauge, Histogram, Counter
import logging

logger = logging.getLogger("Metrics")

# Define Metrics
KALSHI_API_LATENCY = Histogram(
    'kalshi_api_latency_seconds',
    'Latency of Kalshi REST API calls in seconds',
    ['method', 'endpoint']
)
ORDERS_PLACED_TOTAL = Counter(
    "orders_placed_total",
    "Total number of orders attempted to be placed",
    ["ticker", "action", "side"]
)
ORDER_ERRORS_TOTAL = Counter(
    "order_errors_total",
    "Total number of order placement or cancellation errors",
    ["type"]
)
BOT_PNL_CENTS = Gauge(
    "bot_pnl_cents",
    "Current PnL in cents reported by the inventory manager",
    ["ticker"]
)
BOT_INVENTORY_NET_POSITION = Gauge(
    "bot_inventory_net_position",
    "Net YES position for a given market",
    ["ticker"]
)

_server_started = False

def start_metrics_server(port=8000):
    global _server_started
    if not _server_started:
        try:
            start_http_server(port, addr='0.0.0.0')
            logger.info(f"Prometheus metrics server started on 0.0.0.0:{port}")
            _server_started = True
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")

class measure_latency:
    """Context manager to measure latency of Kalshi API calls."""
    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = time.time() - self.start_time
        KALSHI_API_LATENCY.labels(method=self.method, endpoint=self.endpoint).observe(latency)
