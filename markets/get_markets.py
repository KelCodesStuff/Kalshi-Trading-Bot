import requests
import json

url = "https://api.elections.kalshi.com/trade-api/v2/markets?limit=100"

# Perform the GET request
response = requests.get(url)

# Convert the response to a dictionary
# This also validates that the response is actually valid JSON
data = response.json()

# Use json.dumps to format the output
# indent=4 adds spacing, sort_keys=True organizes them alphabetically
pretty_json = json.dumps(data, indent=4)

print(f"Status Code: {response.status_code}")
print(pretty_json)