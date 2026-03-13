# Import standard libraries for HTTP requests and system path manipulation
import requests

# 1. Dynamically add the project root to the system path
# This allows the script in the /orders/ folder to import modules from the root

# 2. Import the centralized authentication function we created
from auth.kalshi_auth import get_auth_headers
from config import BASE_URL

# Define the specific order ID you want to retrieve
order_id = "07a4928b-0745-4352-a684-041644a1a190"

# Define the exact path using the specific order_id for signature generation
sign_path = f"/trade-api/v2/portfolio/orders/{order_id}"

# 3. Generate the required headers using our reusable utility function
# We pass "GET" and the specific path for this request so it signs the correct string
headers = get_auth_headers(method="GET", sign_path=sign_path)

# 4. Execute the GET request against the API URL with the dynamically constructed headers
response = requests.get(BASE_URL + sign_path, headers=headers)

# Check if the request was successful before attempting to parse
if response.status_code == 200:
    # Parse the JSON response into a Python dictionary
    response_data = response.json()

    # Extract the single order object, defaulting to an empty dictionary if missing
    order = response_data.get("order", {})

    # Verify the order object contains data before formatting
    if order:
        # Extract Core Information
        retrieved_id = order.get("order_id")
        ticker = order.get("ticker")
        action = order.get("action", "UNKNOWN").upper()
        side = order.get("side", "UNKNOWN").upper()
        status = order.get("status", "UNKNOWN").upper()

        # Extract Pricing Information
        yes_price = order.get("yes_price", 0)
        no_price = order.get("no_price", 0)
        yes_price_dollars = order.get("yes_price_dollars", "0.0000")
        no_price_dollars = order.get("no_price_dollars", "0.0000")

        # Extract Quantity/Count Information
        initial_count = order.get("initial_count", 0)
        initial_count_fp = order.get("initial_count_fp", "0.00")
        fill_count = order.get("fill_count", 0)
        fill_count_fp = order.get("fill_count_fp", "0.00")

        # Extract Fees and Costs Information
        taker_fees = order.get("taker_fees", 0)
        taker_fees_dollars = order.get("taker_fees_dollars", "0.0000")
        maker_fees = order.get("maker_fees", 0)
        maker_fees_dollars = order.get("maker_fees_dollars", "0.0000")

        taker_fill_cost = order.get("taker_fill_cost", 0)
        taker_fill_cost_dollars = order.get("taker_fill_cost_dollars", "0.0000")
        maker_fill_cost = order.get("maker_fill_cost", 0)
        maker_fill_cost_dollars = order.get("maker_fill_cost_dollars", "0.0000")

        # Print the extracted data in organized, readable blocks
        print("=== ORDER DETAILS ===")
        print(f"Order ID       : {retrieved_id}")
        print(f"Ticker         : {ticker}")
        print(f"Core Details   : {action} {side} | Status: {status}")
        print("-" * 35)

        print("--- Pricing ---")
        print(f"Yes Price      : {yes_price} cents (${yes_price_dollars})")
        print(f"No Price       : {no_price} cents (${no_price_dollars})")
        print("-" * 35)

        print("--- Quantities ---")
        print(f"Initial Count  : {initial_count} (FP: {initial_count_fp})")
        print(f"Fill Count     : {fill_count} (FP: {fill_count_fp})")
        print("-" * 35)

        print("--- Fees & Costs ---")
        print(f"Taker Fees     : {taker_fees} cents (${taker_fees_dollars})")
        print(f"Maker Fees     : {maker_fees} cents (${maker_fees_dollars})")
        print(f"Taker Fill Cost: {taker_fill_cost} cents (${taker_fill_cost_dollars})")
        print(f"Maker Fill Cost: {maker_fill_cost} cents (${maker_fill_cost_dollars})")
        print("=====================\n")
    else:
        print("Order data not found in the response payload.")
else:
    # Print the raw error if the status code is not 200 OK
    print(f"Request failed with Status Code: {response.status_code}")
    print(response.text)