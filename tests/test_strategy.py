import asyncio
import signal
import sys
import random
import requests
import certifi
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from strategy.market_maker import AvellanedaStoikovBot
from execution.kill_switch import KillSwitch


async def main():
    print("Fetching an active market ticker for testing the Strategy...")
    from config import BASE_URL
    r = requests.get(BASE_URL + "/trade-api/v2/markets", params={"limit": 100}, verify=certifi.where())
    active_markets = [m["ticker"] for m in r.json().get("markets", []) if m.get("status") == "active"]
    
    if not active_markets:
        print("No active markets found on Demo.")
        sys.exit(1)
        
    ticker = random.choice(active_markets)
    print(f"Selected Market: {ticker}")
    print("Starting Avellaneda-Stoikov Bot... Press Ctrl+C to Kill.")
    
    # 1. Initialize Bot
    bot = AvellanedaStoikovBot(
        ticker=ticker,
        gamma=0.5, # 0.5 cents skew per 1 contract held
        min_spread=4, # 4 cent minimum profit margin
        order_size=1
    )
    
    # 2. Wire Safety Kill Switch to manual Ctrl+C
    killer = KillSwitch(bot.om)
    def handle_sigint(signum, frame):
        print("\n\n>>> SIGINT. Manual Kill Switch Triggered <<<")
        # Instantly scrub local execution layer 
        killer.trigger_synchronous()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)
    
    # 3. Start Market Maker Loop
    try:
        await bot.start()
    except Exception as e:
        print(f"Bot crashed: {e}")
        # Always trigger safety on crash
        await killer.trigger()

if __name__ == "__main__":
    asyncio.run(main())
