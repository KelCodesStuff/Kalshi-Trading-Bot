"""
Strategy Math Unit Tests

This suite verifies the mathematical correctness of the Avellaneda-Stoikov quoting formula, 
focusing on:
1. Reservation price calculation for neutral, long, and short inventory positions.
2. Optimal bid and ask quoting spreads based on risk aversion (gamma) and min spread parameters.
3. Out-of-bounds price clipping (1c to 99c bounds).
4. Auto-cancellation triggers when orderbooks are empty.
"""

import pytest
import math
from unittest.mock import patch, AsyncMock, MagicMock
from strategy.market_maker import AvellanedaStoikovBot

@pytest.mark.asyncio
async def test_neutral_pricing():
    """When inventory is 0, reservation price should equal the mid price."""
    bot = AvellanedaStoikovBot(ticker="MOCK_TICKER", gamma=0.5, min_spread=4, order_size=1)
    
    # Mock manager inputs
    bot.inv_manager.get_position = MagicMock(return_value=0)
    bot.inv_manager.get_balance = MagicMock(return_value=10000)
    bot.ob_manager.get_best_bid = MagicMock(return_value=(50, 10))
    bot.ob_manager.get_best_ask = MagicMock(return_value=(60, 10))
    
    # Mock output execution
    bot._update_quotes = AsyncMock()
    
    await bot._tick()
    
    # Mid = 55.0, Inv = 0, Gamma = 0.5 -> ResPrice = 55.0
    # Optimal Bid = floor(55 - 2) = 53
    # Optimal Ask = ceil(55 + 2) = 57
    bot._update_quotes.assert_called_once_with(53, 57)

@pytest.mark.asyncio
async def test_long_skew_pricing():
    """When inventory is positive (long YES), reservation price and quotes should skew downward."""
    bot = AvellanedaStoikovBot(ticker="MOCK_TICKER", gamma=0.5, min_spread=4, order_size=1)
    
    bot.inv_manager.get_position = MagicMock(return_value=5) # Holds 5 YES contracts
    bot.inv_manager.get_balance = MagicMock(return_value=10000)
    bot.ob_manager.get_best_bid = MagicMock(return_value=(50, 10))
    bot.ob_manager.get_best_ask = MagicMock(return_value=(60, 10))
    
    bot._update_quotes = AsyncMock()
    
    await bot._tick()
    
    # Mid = 55.0, Inv = 5, Gamma = 0.5 -> ResPrice = 55.0 - (5 * 0.5) = 52.5
    # Optimal Bid = floor(52.5 - 2) = 50
    # Optimal Ask = ceil(52.5 + 2) = 55
    bot._update_quotes.assert_called_once_with(50, 55)

@pytest.mark.asyncio
async def test_short_skew_pricing():
    """When inventory is negative (short YES / holding NO), reservation price and quotes should skew upward."""
    bot = AvellanedaStoikovBot(ticker="MOCK_TICKER", gamma=0.5, min_spread=4, order_size=1)
    
    bot.inv_manager.get_position = MagicMock(return_value=-5) # Short 5 YES contracts
    bot.inv_manager.get_balance = MagicMock(return_value=10000)
    bot.ob_manager.get_best_bid = MagicMock(return_value=(50, 10))
    bot.ob_manager.get_best_ask = MagicMock(return_value=(60, 10))
    
    bot._update_quotes = AsyncMock()
    
    await bot._tick()
    
    # Mid = 55.0, Inv = -5, Gamma = 0.5 -> ResPrice = 55.0 - (-5 * 0.5) = 57.5
    # Optimal Bid = floor(57.5 - 2) = 55
    # Optimal Ask = ceil(57.5 + 2) = 60
    bot._update_quotes.assert_called_once_with(55, 60)

@pytest.mark.asyncio
async def test_bounds_clipping():
    """Quotes should be clipped to Kalshi's boundaries (1c to 99c) and not cross each other."""
    bot = AvellanedaStoikovBot(ticker="MOCK_TICKER", gamma=1.0, min_spread=10, order_size=1)
    
    # Extreme long position skewing reservation price below zero
    bot.inv_manager.get_position = MagicMock(return_value=100) 
    bot.inv_manager.get_balance = MagicMock(return_value=10000)
    bot.ob_manager.get_best_bid = MagicMock(return_value=(50, 10))
    bot.ob_manager.get_best_ask = MagicMock(return_value=(60, 10))
    
    bot._update_quotes = AsyncMock()
    
    await bot._tick()
    
    # Mid = 55.0, Inv = 100, Gamma = 1.0 -> ResPrice = 55 - 100 = -45.0
    # Optimal Bid = floor(-45 - 5) = -50 -> clipped to 1
    # Optimal Ask = ceil(-45 + 5) = -40 -> clipped to 2 (since optimal_ask is min(..., 99) with min boundary 2)
    # Check if bid/ask cross prevention is applied: optimal_bid < optimal_ask. (1 < 2 is valid)
    bot._update_quotes.assert_called_once_with(1, 2)

@pytest.mark.asyncio
async def test_empty_orderbook_handling():
    """If the orderbook is empty, the bot should cancel all active quotes to avoid risk."""
    bot = AvellanedaStoikovBot(ticker="MOCK_TICKER", gamma=0.5, min_spread=4, order_size=1)
    
    bot.inv_manager.get_position = MagicMock(return_value=0)
    bot.inv_manager.get_balance = MagicMock(return_value=10000)
    
    # Simulate empty book
    bot.ob_manager.get_best_bid = MagicMock(return_value=None)
    bot.ob_manager.get_best_ask = MagicMock(return_value=None)
    
    bot._cancel_all_quotes = AsyncMock()
    bot._update_quotes = AsyncMock()
    
    await bot._tick()
    
    bot._cancel_all_quotes.assert_called_once()
    bot._update_quotes.assert_not_called()
