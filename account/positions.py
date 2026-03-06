# positions.py

# Import standard libraries for HTTP requests and system path manipulation
import requests
import sys
from pathlib import Path

# 1. Dynamically add the project root to the system path
# This allows the script in the /balance/ folder to import modules from the root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 2. Import the centralized authentication function we just created
from auth.kalshi_auth import get_auth_headers
from config import BASE_URL

# 3. Define the endpoint path
sign_path = "/trade-api/v2/portfolio/positions"

# 4. Generate the required headers using our reusable utility function
# We pass "GET" and the specific path for this request
headers = get_auth_headers(method="GET", sign_path=sign_path)

# 5. Execute the HTTP request using the dynamically generated headers
query_params = {
    "limit": 100
}
response = requests.get(BASE_URL + sign_path, headers=headers, params=query_params)

# 6. Parse and evaluate the response
if response.status_code == 200:
    # Extract the positions data
    positions_data = response.json()
    market_positions = positions_data.get("market_positions", [])
    event_positions = positions_data.get("event_positions", [])

    # Print the formatted output
    print("=== POSITIONS ===")
    print(f"Status Code : {response.status_code}")
    
    print(f"\nMarket Positions ({len(market_positions)}):")
    for pos in market_positions:
        ticker = pos.get("ticker", "UNKNOWN")
        position = pos.get("position", 0)
        pnl = pos.get("realized_pnl_dollars", "0.00")
        print(f"  Ticker: {ticker} | Position: {position} contracts | PNL: ${pnl}")

    print(f"\nEvent Positions ({len(event_positions)}):")
    for pos in event_positions:
        ticker = pos.get("event_ticker", "UNKNOWN")
        cost = pos.get("total_cost_dollars", "0.00")
        pnl = pos.get("realized_pnl_dollars", "0.00")
        print(f"  Event: {ticker} | Cost: ${cost} | PNL: ${pnl}")
        
    print("===========================")
else:
    # Print error details if the request fails
    print(f"Request failed with Status Code: {response.status_code}")
    print(response.text)