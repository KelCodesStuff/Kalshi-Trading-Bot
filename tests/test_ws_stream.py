import asyncio
import logging

# Provide required imports from our new module

from data.websocket_client import KalshiWebsocketClient
from data.orderbook_manager import OrderbookManager
from data.inventory_manager import InventoryManager

async def main():
    client = KalshiWebsocketClient()
    ob_manager = OrderbookManager(client)
    inv_manager = InventoryManager(client)
    
    # Start the connection loop in the background
    asyncio.create_task(client.connect())
    
    print("Fetching an active market ticker for testing...")
    import requests
    import certifi
    from config import BASE_URL
    
    r = requests.get(BASE_URL + "/trade-api/v2/markets", params={"limit": 100}, verify=certifi.where())
    active_markets = [m["ticker"] for m in r.json().get("markets", []) if m.get("status") == "active"]
    
    if not active_markets:
        print("No active markets found on Demo. Test cannot proceed.")
        sys.exit(1)
        
    import random
    ticker = random.choice(active_markets)
    print(f"Sending subscription for {ticker}...")
    await ob_manager.subscribe([ticker])
    
    print("Hydrating initial portfolio balance and positions...")
    await inv_manager.hydrate()
    print(f"Hydrated Balance is: ${inv_manager.get_balance() / 100:.2f}")
    
    # Subscribe to fills
    print("Subscribing to fill channel...")
    await inv_manager.subscribe()
    
    # Let it run for 5 seconds to gather data
    for i in range(5):
        await asyncio.sleep(1)
        best_bid = ob_manager.get_best_bid(ticker)
        best_ask = ob_manager.get_best_ask(ticker)
        pos = inv_manager.get_position(ticker)
        print(f"[{i+1}s] Best Bid: {best_bid} | Best Ask: {best_ask} | Pos: {pos}")
        
    print("Done testing.")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
