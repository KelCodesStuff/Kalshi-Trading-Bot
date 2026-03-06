# Import required standard libraries
import json
import uuid
import requests
import sys
from pathlib import Path

# 1. Dynamically add the project root to the system path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from auth.kalshi_auth import get_auth_headers
from config import BASE_URL

# 3. Define the exact endpoint path for order creation
sign_path = "/trade-api/v2/portfolio/orders"

# 4. Generate the required headers using our reusable utility function
headers = get_auth_headers(method="POST", sign_path=sign_path)
headers["Content-Type"] = "application/json" # Required for POST requests with JSON bodies

# 9. Define the payload for a strict Maker Limit Order
payload = {
    "ticker": "KXNBAGAME-26FEB24PHIIND-PHI", # Valid target market
    "action": "buy",
    "side": "yes",
    "type": "limit", # Must be 'limit' to act as a maker
    "count": 2, # Number of contracts to purchase
    "yes_price": 10, # Bidding very low (10 cents) ensures it does not cross the spread immediately
    "client_order_id": str(uuid.uuid4()), # Generate a unique UUID for idempotency
    "post_only": True # Mathematically guarantees Maker status; rejects if it would execute as a Taker
}

# 10. Execute the POST request against the API URL with headers and JSON payload
response = requests.post(BASE_URL + sign_path, json=payload, headers=headers)

# 11. Parse and format the response output
print(f"Status Code: {response.status_code}")
if response.status_code == 201:
    print("Order Successfully Created:")
    print(json.dumps(response.json(), indent=4))
else:
    print("Failed to create order:")
    print(response.text)