"""
Inventory Manager Unit Tests

This suite verifies that execution fill messages are correctly processed by the InventoryManager 
class to maintain an accurate local record of:
1. USD Balance in cents.
2. Net contract inventory position (positive for long YES, negative for short YES / long NO).
"""

import pytest
from unittest.mock import MagicMock
from data.inventory_manager import InventoryManager

def test_inventory_buy_yes_fill():
    """Buying YES contracts should reduce balance and increase position."""
    mock_client = MagicMock()
    manager = InventoryManager(mock_client)
    manager.balance_cents = 10000 # $100.00
    manager.positions = {"MOCK_TICKER": 0}
    
    fill_msg = {
        "type": "fill",
        "msg": {
            "market_ticker": "MOCK_TICKER",
            "action": "buy",
            "side": "yes",
            "count": 10,
            "price": 50 # 50 cents per share
        }
    }
    
    manager._handle_fill(fill_msg["msg"])
    
    # 10 contracts * 50 cents = 500 cents cost -> New Balance: 9500 cents
    assert manager.get_balance() == 9500
    # Net position should be +10
    assert manager.get_position("MOCK_TICKER") == 10

def test_inventory_sell_yes_fill():
    """Selling YES contracts should increase balance and decrease position."""
    mock_client = MagicMock()
    manager = InventoryManager(mock_client)
    manager.balance_cents = 10000
    manager.positions = {"MOCK_TICKER": 10}
    
    fill_msg = {
        "type": "fill",
        "msg": {
            "market_ticker": "MOCK_TICKER",
            "action": "sell",
            "side": "yes",
            "count": 5,
            "price": 60
        }
    }
    
    manager._handle_fill(fill_msg["msg"])
    
    # 5 contracts * 60 cents = 300 cents revenue -> New Balance: 10300 cents
    assert manager.get_balance() == 10300
    # Net position should decrease by 5 -> New Position: +5
    assert manager.get_position("MOCK_TICKER") == 5

def test_inventory_buy_no_fill():
    """Buying NO contracts should reduce balance and decrease net YES-equivalent position."""
    mock_client = MagicMock()
    manager = InventoryManager(mock_client)
    manager.balance_cents = 10000
    manager.positions = {"MOCK_TICKER": 0}
    
    fill_msg = {
        "type": "fill",
        "msg": {
            "market_ticker": "MOCK_TICKER",
            "action": "buy",
            "side": "no",
            "count": 5,
            "price": 40
        }
    }
    
    manager._handle_fill(fill_msg["msg"])
    
    # 5 contracts * 40 cents = 200 cents cost -> New Balance: 9800 cents
    assert manager.get_balance() == 9800
    # Buying NO is equivalent to shorting YES -> New Net Position: -5
    assert manager.get_position("MOCK_TICKER") == -5

def test_inventory_sell_no_fill():
    """Selling NO contracts should increase balance and increase net YES-equivalent position."""
    mock_client = MagicMock()
    manager = InventoryManager(mock_client)
    manager.balance_cents = 10000
    manager.positions = {"MOCK_TICKER": -10}
    
    fill_msg = {
        "type": "fill",
        "msg": {
            "market_ticker": "MOCK_TICKER",
            "action": "sell",
            "side": "no",
            "count": 5,
            "price": 40
        }
    }
    
    manager._handle_fill(fill_msg["msg"])
    
    # 5 contracts * 40 cents = 200 cents revenue -> New Balance: 10200 cents
    assert manager.get_balance() == 10200
    # Selling NO decreases your short position -> New Net Position: -5
    assert manager.get_position("MOCK_TICKER") == -5
