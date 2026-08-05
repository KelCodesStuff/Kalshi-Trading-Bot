"""
Inventory Acquisition Utility Script

This helper utility script is designed to rapidly build up inventory for testing. 
It places a configured number of individual 1-contract YES buy orders at 99 cents 
to cross the spread immediately and guarantee quick fills.
"""

import asyncio
from execution.order_manager import OrderManager
import sys

async def main():
    ticker = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    om = OrderManager()
    print(f"Placing {count} individual buy orders at 99c for {ticker}...")
    
    successes = 0
    # Place individual 1-contract orders at 99c to guarantee crossing the spread
    for i in range(count):
        client_id = await om.place_order(ticker, side="yes", action="buy", count=1, price=99)
        if client_id:
            successes += 1
    
    print(f"Placed {successes}/{count} fill orders successfully.")

if __name__ == "__main__":
    asyncio.run(main())
