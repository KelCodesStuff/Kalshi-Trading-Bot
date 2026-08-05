"""
Orderbook Manager Unit Tests

This suite verifies that L2 orderbook updates and price conversions are handled correctly by 
the OrderbookManager class:
1. Parsing full snapshots for 'yes' and 'no' shares.
2. Appending and reducing volumes via orderbook delta updates.
3. Removing price levels completely when quantities drop to 0 or below.
4. Computing implied YES ask prices from the highest resting NO bid prices.
"""

import pytest
from unittest.mock import MagicMock
from data.orderbook_manager import OrderbookManager

def test_orderbook_snapshot_parsing():
    """Verify that snapshots hydrate the books structure correctly."""
    mock_client = MagicMock()
    manager = OrderbookManager(mock_client)
    
    snapshot_msg = {
        "type": "orderbook_snapshot",
        "msg": {
            "market_ticker": "MOCK_TICKER",
            "yes": [[50, 10], [49, 15]],
            "no": [[45, 5], [44, 8]]
        }
    }
    
    # Process snapshot
    manager._handle_snapshot(snapshot_msg["msg"])
    
    # Assert book structure was loaded correctly
    assert manager.books["MOCK_TICKER"]["yes"] == {50: 10, 49: 15}
    assert manager.books["MOCK_TICKER"]["no"] == {45: 5, 44: 8}
    
    # Check best bids/asks
    assert manager.get_best_bid("MOCK_TICKER") == (50, 10)
    # Highest NO bid = 45 -> Implied YES Ask = 100 - 45 = 55
    assert manager.get_best_ask("MOCK_TICKER") == (55, 5)

def test_orderbook_delta_processing():
    """Verify that delta events add, subtract, and remove price levels correctly."""
    mock_client = MagicMock()
    manager = OrderbookManager(mock_client)
    
    # 1. Initialize with snapshot
    manager._handle_snapshot({
        "market_ticker": "MOCK_TICKER",
        "yes": [[50, 10]],
        "no": [[45, 5]]
    })
    
    # 2. Add delta to existing YES level
    manager._handle_delta({
        "market_ticker": "MOCK_TICKER",
        "side": "yes",
        "price": 50,
        "delta": 5
    })
    assert manager.books["MOCK_TICKER"]["yes"][50] == 15
    
    # 3. Add delta to new YES level
    manager._handle_delta({
        "market_ticker": "MOCK_TICKER",
        "side": "yes",
        "price": 51,
        "delta": 2
    })
    assert manager.books["MOCK_TICKER"]["yes"][51] == 2
    assert manager.get_best_bid("MOCK_TICKER") == (51, 2)
    
    # 4. Subtract delta to remove a level completely
    manager._handle_delta({
        "market_ticker": "MOCK_TICKER",
        "side": "yes",
        "price": 51,
        "delta": -2
    })
    # Level should be popped from dict
    assert 51 not in manager.books["MOCK_TICKER"]["yes"]
    assert manager.get_best_bid("MOCK_TICKER") == (50, 15)
