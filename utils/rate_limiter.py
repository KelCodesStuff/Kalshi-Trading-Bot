"""
Asynchronous Token Bucket Rate Limiter

This module implements a token bucket algorithm to throttle REST client calls. 
It ensures compliance with Kalshi API limit constraints (e.g. max 10 requests per second) 
by pausing execution tasks when tokens are exhausted.
"""

import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    An asynchronous Token Bucket rate limiter.
    """
    def __init__(self, rate: float, per: float):
        """
        :param rate: Number of tokens added per time interval
        :param per: Time interval in seconds
        """
        self.rate = rate
        self.per = per
        self.capacity = rate
        self._tokens = self.capacity
        self._last_update = time.monotonic()
        # A lock to ensure async safety when updating tokens
        self._lock = asyncio.Lock()

    async def acquire(self):
        """
        Wait until a token is available, then consume it.
        """
        while True:
            async with self._lock:
                now = time.monotonic()
                
                # Calculate how many tokens we should add based on elapsed time
                elapsed = now - self._last_update
                new_tokens = elapsed * (self.rate / self.per)
                
                if new_tokens > 0:
                    self._tokens = min(self.capacity, self._tokens + new_tokens)
                    self._last_update = now
                
                # If a token is available, consume it and return
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                
                # If no token is available, calculate how long to wait for exactly 1 token
                wait_time = (1.0 - self._tokens) / (self.rate / self.per)
            
            # Wait outside the lock so other coroutines can attempt to acquire
            await asyncio.sleep(wait_time)
