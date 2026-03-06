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
    def __init__(self):
        # Maps client_order_id -> Order Dict
        self.active_orders: Dict[str, Dict[str, Any]] = {}

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
        
        # Perform REST request without blocking the async loop
        response = await asyncio.to_thread(self._post_request, sign_path, payload)
        
        if response is not None and response.status_code == 201:
            logger.info(f"Order Placed: {action} {count} {side} @ {price}c for {ticker} (ID: {client_order_id})")
            
            self.active_orders[client_order_id] = {
                "ticker": ticker,
                "side": side,
                "action": action,
                "count": count,
                "price": price,
                "kalshi_order_id": response.json().get("order", {}).get("order_id")
            }
            return client_order_id
        else:
            err_text = response.text if response is not None else "No response"
            logger.error(f"Failed to place order: {payload}. Error: {err_text}")
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
        
        response = await asyncio.to_thread(self._delete_request, sign_path)
        
        if response is not None and response.status_code in [200, 204]:
            logger.info(f"Order Cancelled: {client_order_id}")
            self.active_orders.pop(client_order_id, None)
            return True
        elif response is not None and response.status_code == 404:
            # Order might already be filled or cancelled
            logger.info(f"Order {client_order_id} not found on server (may be filled/cancelled already).")
            self.active_orders.pop(client_order_id, None)
            return True
        else:
            err_text = response.text if response is not None else "No response"
            logger.error(f"Failed to cancel order {client_order_id}. Error: {err_text}")
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
