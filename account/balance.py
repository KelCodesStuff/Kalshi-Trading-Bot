# balance.py

# Import standard libraries for HTTP requests and system path manipulation
import requests

# 1. Dynamically add the project root to the system path
# This allows the script in the /balance/ folder to import modules from the root

# 2. Import the centralized authentication function we just created
from auth.kalshi_auth import get_auth_headers
from config import BASE_URL

# 3. Define the endpoint path
sign_path = "/trade-api/v2/portfolio/balance"

# 4. Generate the required headers using our reusable utility function
# We pass "GET" and the specific path for this request
headers = get_auth_headers(method="GET", sign_path=sign_path)

# 5. Execute the HTTP request using the dynamically generated headers
response = requests.get(BASE_URL + sign_path, headers=headers)

# 6. Parse and evaluate the response
if response.status_code == 200:
    # Extract the balance data
    balance_data = response.json()
    balance_cents = balance_data.get("balance", 0)
    balance_dollars = balance_cents / 100.0

    # Print the formatted output
    print("=== ACCOUNT BALANCE ===")
    print(f"Status Code : {response.status_code}")
    print(f"Total Funds : {balance_cents} cents (${balance_dollars:.2f})")
    print("=======================")
else:
    # Print error details if the request fails
    print(f"Request failed with Status Code: {response.status_code}")
    print(response.text)