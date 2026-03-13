import sys
from pathlib import Path

# Add project root to sys.path directly
root = str(Path(__file__).resolve().parent.parent)
if root not in sys.path:
    sys.path.insert(0, root)

from config import BASE_URL
from auth.kalshi_auth import get_auth_headers

import logging
import requests
import asyncio
import uuid
import certifi
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from utils.rate_limiter import RateLimiter
from utils.metrics import measure_latency, ORDERS_PLACED_TOTAL, ORDER_ERRORS_TOTAL

logger = logging.getLogger("OrderManager")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class OrderManager:
    """
    Handles placing, replacing, and canceling discrete Limit orders via Kalshi REST API.
    Maintains a local lightweight record of active order IDs.
    """
    def __init__(self, db_path: str = "orders.db"):
        # Maps client_order_id -> Order Dict
        self.active_orders: Dict[str, Dict[str, Any]] = {}

        # Initialize SQLite database
        self.db_path = db_path
        self._init_db()

        # Kalshi Rate Limit: 10 requests per second
        self.rate_limiter = RateLimiter(rate=10, per=1.0)

    def _init_db(self):
        """Initializes the SQLite database table for order tracking."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    client_order_id TEXT PRIMARY KEY,
                    kalshi_order_id TEXT,
                    ticker TEXT,
                    action TEXT,
                    side TEXT,
                    price INTEGER,
                    count INTEGER,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.commit()

    def _update_db_order_status(self, client_order_id: str, status: str, kalshi_order_id: str = None, order_details: dict = None):
        """Updates or inserts an order record into the SQLite database."""
        now = datetime.datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if order exists
            cursor.execute("SELECT client_order_id FROM orders WHERE client_order_id = ?", (client_order_id,))
            exists = cursor.fetchone()
            
            if exists:
                if kalshi_order_id:
                    cursor.execute('''
                        UPDATE orders 
                        SET status = ?, kalshi_order_id = ?, updated_at = ?
                        WHERE client_order_id = ?
                    ''', (status, kalshi_order_id, now, client_order_id))
                else:
                    cursor.execute('''
                        UPDATE orders 
                        SET status = ?, updated_at = ?
                        WHERE client_order_id = ?
                    ''', (status, now, client_order_id))
            elif order_details:
                cursor.execute('''
                    INSERT INTO orders (
                        client_order_id, kalshi_order_id, ticker, action, side, 
                        price, count, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_order_id, 
                    kalshi_order_id, 
                    order_details.get("ticker"), 
                    order_details.get("action"), 
                    order_details.get("side"), 
                    order_details.get("price"), 
                    order_details.get("count"), 
                    status, 
                    now, 
                    now
                ))
            conn.commit()

    async def place_order(self, ticker: str, side: str, action: str, count: int, price: int) -> Optional[str]:
        """
        Place a new order.
        side: "yes" or "no"
        action: "buy" or "sell"
        count: number of contracts
        price: limit price in cents (1-99)
        Returns the client_order_id if successful, None otherwise.
        """
        client_order_id = str(uuid.uuid4())
        
        payload = {
            "action": action,
            "side": side,
            "count": count,
            "type": "limit",
            "ticker": ticker,
            "client_order_id": client_order_id,
            "yes_price": price if side == "yes" else None,
            "no_price": price if side == "no" else None
        }
        
        # Remove null values to avoid API schema errors
        payload = {k: v for k, v in payload.items() if v is not None}
        
        sign_path = "/trade-api/v2/portfolio/orders"
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            # 1. Wait for token to enforce overall rate limit
            await self.rate_limiter.acquire()
            
            # 2. Perform REST request without blocking the async loop
            response = await asyncio.to_thread(self._post_request, sign_path, payload)
            
            if response is not None:
                if response.status_code == 201:
                    logger.info(f"Order Placed: {action} {count} {side} @ {price}c for {ticker} (ID: {client_order_id})")
                    ORDERS_PLACED_TOTAL.labels(ticker=ticker, action=action, side=side).inc()
                    
                    self.active_orders[client_order_id] = {
                        "ticker": ticker,
                        "side": side,
                        "action": action,
                        "count": count,
                        "price": price,
                        "kalshi_order_id": response.json().get("order", {}).get("order_id")
                    }
                    
                    # Persist to database
                    self._update_db_order_status(
                        client_order_id, 
                        "resting", 
                        kalshi_order_id=self.active_orders[client_order_id]["kalshi_order_id"],
                        order_details=self.active_orders[client_order_id]
                    )
                    
                    return client_order_id
                
                elif response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited (429) placing order. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue # Retry
                    else:
                        logger.error(f"Failed to place order after {max_retries} retries due to rate limits.")
                        ORDER_ERRORS_TOTAL.labels(type="place_rate_limit").inc()
                        return None
                
            err_text = response.text if response is not None else "No response"
            logger.error(f"Failed to place order: {payload}. Error: {err_text}")
            ORDER_ERRORS_TOTAL.labels(type="place_api_error").inc()
            return None

    async def cancel_order(self, client_order_id: str) -> bool:
        """
        Cancel an existing order by its ID.
        Returns True if successfully cancelled/already cancelled, False on error.
        """
        if client_order_id not in self.active_orders:
            logger.warning(f"Order {client_order_id} not found in active orders.")
            # Note: order might have filled, or tracker lost it.
            # We could still try to cancel it if we really wanted to.
        
        order_to_cancel = self.active_orders.get(client_order_id)
        if order_to_cancel and order_to_cancel.get("kalshi_order_id"):
            # V2 API uses the actual order_id returned by Kalshi, not client_order_id, for cancellations
            order_id = order_to_cancel["kalshi_order_id"]
        else:
            # Fallback (Kalshi V2 usually expects `order_id` in the URL path)
            order_id = client_order_id
            
        sign_path = f"/trade-api/v2/portfolio/orders/{order_id}"
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            # 1. Wait for token to enforce overall rate limit
            await self.rate_limiter.acquire()
            
            response = await asyncio.to_thread(self._delete_request, sign_path)
            
            if response is not None:
                if response.status_code in [200, 204]:
                    logger.info(f"Order Cancelled: {client_order_id}")
                    self.active_orders.pop(client_order_id, None)
                    self._update_db_order_status(client_order_id, "cancelled")
                    return True
                elif response.status_code == 404:
                    # Order might already be filled or cancelled
                    logger.info(f"Order {client_order_id} not found on server (may be filled/cancelled already).")
                    self.active_orders.pop(client_order_id, None)
                    self._update_db_order_status(client_order_id, "cancelled_or_filled_404")
                    return True
                elif response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited (429) canceling order. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue # Retry
                    else:
                        logger.error(f"Failed to cancel order after {max_retries} retries due to rate limits.")
                        ORDER_ERRORS_TOTAL.labels(type="cancel_rate_limit").inc()
                        return False
            
            err_text = response.text if response is not None else "No response"
            logger.error(f"Failed to cancel order {client_order_id}. Error: {err_text}")
            ORDER_ERRORS_TOTAL.labels(type="cancel_api_error").inc()
            return False

    def _post_request(self, sign_path: str, payload: dict) -> Optional[requests.Response]:
        """Synchronous wrapper for POST requests"""
        try:
            # get_auth_headers needs the path and method
            headers = get_auth_headers(method="POST", sign_path=sign_path)
            # Kalshi API expects content-type to be application/json
            headers["Content-Type"] = "application/json"
            
            import json
            json_payload = json.dumps(payload, separators=(',', ':'))
            
            logger.info(f"POST {BASE_URL + sign_path} payload: {json_payload}")
            with measure_latency("POST", sign_path):
                resp = requests.post(
                    BASE_URL + sign_path,
                    data=json_payload,
                    headers=headers,
                    timeout=10,
                    verify=certifi.where()
                )
            logger.info(f"POST Response: {resp.status_code} - {resp.text}")
            return resp
        except Exception as e:
            import traceback
            logger.error(f"POST Request Exception: {e}\n{traceback.format_exc()}")
            return None

    def _delete_request(self, sign_path: str) -> Optional[requests.Response]:
        """Synchronous wrapper for DELETE requests"""
        try:
            headers = get_auth_headers(method="DELETE", sign_path=sign_path)
            with measure_latency("DELETE", "/trade-api/v2/portfolio/orders"):
                return requests.delete(
                    BASE_URL + sign_path,
                    headers=headers,
                    timeout=10,
                    verify=certifi.where()
                )
        except Exception as e:
            logger.error(f"DELETE Request Exception: {e}")
            return None

    def get_tracked_active_orders(self, ticker: str = None) -> List[Dict[str, Any]]:
        """Return list of active orders we are currently tracking, optionally filtered by ticker."""
        orders = []
        for cid, details in self.active_orders.items():
            if not ticker or details.get("ticker") == ticker:
                order_copy = dict(details)
                order_copy["client_order_id"] = cid
                orders.append(order_copy)
        return orders

    async def sync_and_recover_state(self):
        """
        Fetches all resting orders from the REST API and cancels them.
        This ensures that when the bot starts, it doesn't leave orphaned orders
        from a previous crashed run.
        """
        logger.info("Starting state recovery and reconciliation...")
        
        sign_path = "/trade-api/v2/portfolio/orders"
        query_params = {"status": "resting", "limit": 100}
        
        try:
            # Need to build query string for signature if it contains params, but for Kalshi V2,
            # the signature is usually just on the path. We will use the requests library to handle params.
            # But get_auth_headers needs the path without params for the signature, let's keep it simple.
            headers = get_auth_headers(method="GET", sign_path=sign_path)
            
            # Wrap the cross-thread call to still capture overall latency
            with measure_latency("GET", "/trade-api/v2/portfolio/orders"):
                response = await asyncio.to_thread(
                    requests.get,
                    BASE_URL + sign_path,
                    headers=headers,
                    params=query_params,
                    timeout=10,
                    verify=certifi.where()
                )
                
            if response.status_code == 200:
                orders_list = response.json().get("orders", [])
                logger.info(f"Found {len(orders_list)} resting orders on Kalshi.")
                
                cancel_tasks = []
                for order in orders_list:
                    order_id = order.get("order_id")
                    client_order_id = order.get("client_order_id")
                    logger.info(f"Preparing to cancel orphaned order: {order_id} (Client ID: {client_order_id})")
                    
                    # We can use the REST API directly to cancel by Kalshi order_id to be safe
                    cancel_path = f"/trade-api/v2/portfolio/orders/{order_id}"
                    
                    # Create a quick async wrapper for the deletion
                    async def _do_cancel(p, cid):
                        resp = await asyncio.to_thread(self._delete_request, p)
                        if resp and resp.status_code in [200, 204]:
                            logger.info(f"Successfully cancelled orphaned order {p}")
                            if cid:
                                self._update_db_order_status(cid, "cancelled", kalshi_order_id=order_id)
                        else:
                            err = resp.text if resp else "No response"
                            logger.error(f"Failed to cancel orphaned order {p}: {err}")
                            
                    cancel_tasks.append(_do_cancel(cancel_path, client_order_id))
                    
                if cancel_tasks:
                    logger.info(f"Executing {len(cancel_tasks)} cancellation tasks...")
                    await asyncio.gather(*cancel_tasks, return_exceptions=True)
                    logger.info("State recovery and reconciliation complete.")
                else:
                    logger.info("No orphaned resting orders found. State is clean.")
            else:
                logger.error(f"Failed to fetch resting orders during recovery. Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            import traceback
            logger.error(f"Exception during state recovery: {e}\n{traceback.format_exc()}")
