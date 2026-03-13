import asyncio
import signal
import json


from execution.order_manager import OrderManager
from execution.kill_switch import KillSwitch

async def main():
    print("Initializing components...")
    om = OrderManager()
    killer = KillSwitch(om)
    
    # Setup Signal Handler for Manual Trigger (Ctrl+C)
    def handle_sigint(signum, frame):
        print("\n\n>>> SIGINT RECEIVED. Manual Kill Switch Triggered <<<")
        killer.trigger_synchronous()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, handle_sigint)
    print("Kill Switch armed. Press Ctrl+C to test manual trigger.")

    # 1. Fetch an active market to ensure we have a valid environment
    print("Fetching an active market ticker for testing...")
    import requests
    import certifi
    from config import BASE_URL
    
    r = requests.get(BASE_URL + "/trade-api/v2/markets", params={"limit": 100}, verify=certifi.where())
    active_markets = [m["ticker"] for m in r.json().get("markets", []) if m.get("status") == "active"]
    
    if not active_markets:
        print("No active markets found on Demo. Test cannot proceed.")
        return
        
    import random
    ticker = random.choice(active_markets)
    
    # 2. Add an order that won't execute immediately (1 cent YES)
    print(f"Placing dummy order on {ticker}...")
    order_id_1 = await om.place_order(ticker, side="yes", action="buy", count=1, price=1)
    
    if not order_id_1:
        print("Failed to place dummy order. Test aborted.")
        return

    print(f"Order successfully placed: {order_id_1}")
    print(f"Active orders before Kill Switch: {len(om.active_orders)}")
    
    print("\nSimulating unexpected failure, invoking async Kill Switch...")
    # 3. Trigger the asynchronous kill switch
    await killer.trigger()
    
    print(f"Active orders after Kill Switch: {len(om.active_orders)}")

if __name__ == "__main__":
    asyncio.run(main())
