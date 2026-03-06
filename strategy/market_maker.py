import asyncio
import logging
import time
import math
from typing import Optional

from data.websocket_client import KalshiWebsocketClient
from data.orderbook_manager import OrderbookManager
from data.inventory_manager import InventoryManager
from execution.order_manager import OrderManager

logger = logging.getLogger("MarketMaker")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class AvellanedaStoikovBot:
    """
    Implements a simplified Avellaneda-Stoikov market making algorithm for Kalshi.
    
    Formula:
    R (Reservation Price) = Mid_Price - (Inventory * Risk_Aversion)
    Bid = R - (Spread / 2)
    Ask = R + (Spread / 2)
    """
    def __init__(
        self, 
        ticker: str, 
        gamma: float = 0.5, # Risk aversion. How much 1 contract skews our price (in cents).
        min_spread: int = 4, # Minimum spread to quote (in cents).
        order_size: int = 1   # Number of contracts to quote on each side.
    ):
        self.ticker = ticker
        self.gamma = gamma 
        self.min_spread = min_spread
        self.order_size = order_size
        
        # Core Managers
        self.ws_client = KalshiWebsocketClient()
        self.ob_manager = OrderbookManager(self.ws_client)
        self.inv_manager = InventoryManager(self.ws_client)
        self.om = OrderManager()
        
        self.running = False
        
        # State tracking for our active quotes
        self.current_bid_id: Optional[str] = None
        self.current_ask_id: Optional[str] = None
        
        self.current_bid_price: Optional[int] = None
        self.current_ask_price: Optional[int] = None

    async def start(self):
        """Initializes infrastructure and starts the main trading loop."""
        logger.info(f"Starting Market Maker for {self.ticker}")
        
        # 1. Start the WebSocket Connection
        asyncio.create_task(self.ws_client.connect())
        
        # 2. Wait for connection to establish
        while not self.ws_client.is_connected:
            await asyncio.sleep(0.1)
            
        logger.info("WebSocket Connected. Hydrating state...")
        
        # 3. Hydrate initial inventory and subscribe to channels
        await self.inv_manager.hydrate()
        await self.inv_manager.subscribe()
        await self.ob_manager.subscribe([self.ticker])
        
        logger.info("State hydrated. Beginning quoting loop.")
        self.running = True
        
        # 4. Enter Main Loop
        try:
            while self.running:
                await self._tick()
                await asyncio.sleep(1) # Re-evaluate every 1 second
        except asyncio.CancelledError:
            logger.info("Market Maker stopped.")
        except Exception as e:
            logger.error(f"Fatal error in trading loop: {e}", exc_info=True)
            self.running = False

    async def _tick(self):
        """The core logic evaluated every cycle."""
        
        best_bid = self.ob_manager.get_best_bid(self.ticker)
        best_ask = self.ob_manager.get_best_ask(self.ticker)
        
        if not best_bid or not best_ask:
            # Orderbook is empty on one or both sides, unsafe to calculate mid-price.
            # In a production system, we might use a theoretical model here.
            # For this MVP, we withdraw quotes.
            await self._cancel_all_quotes()
            return

        bid_price = best_bid[0]
        ask_price = best_ask[0]
        
        # 1. Calculate Mid Price
        mid_price = (bid_price + ask_price) / 2.0
        
        # 2. Get Inventory
        # Convention: positive inventory = holding net YES
        inventory = self.inv_manager.get_position(self.ticker)
        
        # 3. Calculate Reservation Price (R)
        # R = M - (q * gamma)
        reservation_price = mid_price - (inventory * self.gamma)
        
        # 4. Calculate Optimal Optimal Bid/Ask
        optimal_bid = math.floor(reservation_price - (self.min_spread / 2.0))
        optimal_ask = math.ceil(reservation_price + (self.min_spread / 2.0))
        
        # Ensure prices fit within Kalshi bounds (1c to 99c)
        optimal_bid = max(1, min(optimal_bid, 98))
        optimal_ask = max(2, min(optimal_ask, 99))
        
        # Ensure we don't cross the spread against ourselves
        if optimal_bid >= optimal_ask:
            optimal_bid = optimal_ask - 1
            
        logger.debug(f"[STATE] Mid: {mid_price:.2f} | Inv: {inventory} | Res Price: {reservation_price:.2f}")
            
        # 5. Execute Output
        await self._update_quotes(optimal_bid, optimal_ask)

    async def _update_quotes(self, new_bid: int, new_ask: int):
        """Places or replaces quotes if the optimal prices have shifted."""
        tasks = []
        
        # Handle BID Side
        if new_bid != self.current_bid_price:
            if self.current_bid_id:
                tasks.append(self.om.cancel_order(self.current_bid_id))
            logger.info(f">> Placing new BID: {self.order_size} YES @ {new_bid}c")
            self.current_bid_id = await self.om.place_order(
                ticker=self.ticker, side="yes", action="buy", count=self.order_size, price=new_bid
            )
            self.current_bid_price = new_bid if self.current_bid_id else None

        # Handle ASK Side (Selling YES contracts)
        if new_ask != self.current_ask_price:
            if self.current_ask_id:
                tasks.append(self.om.cancel_order(self.current_ask_id))
            logger.info(f">> Placing new ASK: {self.order_size} YES @ {new_ask}c")
            self.current_ask_id = await self.om.place_order(
                ticker=self.ticker, side="yes", action="sell", count=self.order_size, price=new_ask
            )
            self.current_ask_price = new_ask if self.current_ask_id else None
            
        # Execute any required cancellations asynchronously
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _cancel_all_quotes(self):
        """Withdraws all active quotes from the market."""
        tasks = []
        if self.current_bid_id:
            tasks.append(self.om.cancel_order(self.current_bid_id))
            self.current_bid_id = None
            self.current_bid_price = None
        if self.current_ask_id:
            tasks.append(self.om.cancel_order(self.current_ask_id))
            self.current_ask_id = None
            self.current_ask_price = None
            
        if tasks:
            logger.info("Withdrawing quotes...")
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def stop(self):
        self.running = False
        await self._cancel_all_quotes()
