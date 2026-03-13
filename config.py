import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Environment (Options: "demo" or "prod")
ENVIRONMENT = os.getenv("KALSHI_ENV", "demo")

# Base URLs
if ENVIRONMENT == "prod":
    BASE_URL = "https://api.elections.kalshi.com"
else:
    BASE_URL = "https://demo-api.kalshi.co"

# API Authentication configuration
API_KEY = os.getenv("KALSHI_API_KEY")

if not API_KEY:
    raise ValueError("KALSHI_API_KEY environment variable is not set!")

# Private key path
# Use a different default key file for production, or allow overriding via environment variable
default_key_filename = "kalshi_private_key_prod.pem" if ENVIRONMENT == "prod" else "kalshi_private_key_demo.pem"
PRIVATE_KEY_PATH = Path(os.getenv("KALSHI_PRIVATE_KEY_PATH", PROJECT_ROOT / default_key_filename))

# Alerting
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "https://hooks.slack.com/services/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")

# Strategy Tuning Parameters
# Default: Gamma 0.5 (Risk Aversion), 4 cent minimum spread, 1 contract order size
RISK_GAMMA = float(os.getenv("RISK_GAMMA", "0.5"))
MIN_SPREAD = int(os.getenv("MIN_SPREAD", "4"))
ORDER_SIZE = int(os.getenv("ORDER_SIZE", "1"))
TARGET_TICKER = os.getenv("TARGET_TICKER", "") # Can be injected to force a specific market
