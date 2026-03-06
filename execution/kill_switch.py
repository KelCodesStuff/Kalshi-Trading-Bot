import logging
import asyncio
import requests
import certifi

from config import BASE_URL
from auth.kalshi_auth import get_auth_headers
from execution.order_manager import OrderManager

logger = logging.getLogger("KillSwitch")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class KillSwitch:
    """
    A unified kill switch layer for the market making application.
    Capable of cancelling known active orders instantly to drop exposure.
    """
    def __init__(self, order_manager: OrderManager):
        self.om = order_manager

    def trigger_synchronous(self):
        """Immediately cancel all known local orders synchronously."""
        logger.warning("KILL SWITCH TRIGGERED (Sync). Canceling all local orders...")
        active_ids = list(self.om.active_orders.keys())
        
        if not active_ids:
            logger.info("No active local orders to kill.")
            return
            
        for order_id in active_ids:
            logger.warning(f"Canceling {order_id}...")
            # Fire an emergency blocking cancel to Kalshi using the raw request wrapper
            sign_path = f"/trade-api/v2/portfolio/orders/{order_id}"
            try:
                headers = get_auth_headers(method="DELETE", sign_path=sign_path)
                resp = requests.delete(
                    BASE_URL + sign_path, 
                    headers=headers, 
                    timeout=5, 
                    verify=certifi.where()
                )
                if resp.status_code in [200, 204]:
                    logger.info(f"Successfully killed {order_id}")
                    self.om.active_orders.pop(order_id, None)
                elif resp.status_code == 404:
                    logger.info(f"Order {order_id} already closed/filled.")
                    self.om.active_orders.pop(order_id, None)
                else:
                    logger.error(f"Failed to kill {order_id}: {resp.status_code} - {resp.text}")
            except Exception as e:
                import traceback
                logger.error(f"Exception while killing {order_id}: {e}\n{traceback.format_exc()}")

    async def trigger(self):
        """Asynchronously triggers the kill switch using the core order manager."""
        logger.warning("KILL SWITCH TRIGGERED (Async). Canceling all local orders...")
        active_ids = list(self.om.active_orders.keys())
        
        if not active_ids:
            logger.info("No active local orders to kill.")
            return

        tasks = []
        for order_id in active_ids:
            tasks.append(self.om.cancel_order(order_id))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for order_id, res in zip(active_ids, results):
            if isinstance(res, Exception):
                logger.error(f"Exception encountered attempting to kill {order_id}: {res}")
            elif not res:
                logger.error(f"Failed to kill {order_id} (API rejected)")
            else:
                logger.info(f"Successfully completed cancellation of {order_id}")
