# Kalshi Algorithmic Market Maker Bot

This project is a fully-functional algorithmic **market-making trading bot** built for the Kalshi prediction market platform. Its primary goal is to provide dual-sided liquidity (bids and asks) on Kalshi markets to capture the bid-ask spread while actively managing inventory risk.

## System Architecture

The trading bot is composed of several core modules:

### 1. Authentication & Configuration (`auth/`, `config.py`)
- **`config.py`**: Manages environment variables (Demo vs. Production), API keys, and RSA private key path configurations.
- **`auth/kalshi_auth.py`**: Implements the required RSA-PSS cryptographic signatures to securely authenticate with Kalshi's V2 REST and WebSocket APIs.

### 2. Market Data & State Management (`data/`)
- **`websocket_client.py`**: An asynchronous WebSocket client that maintains a persistent, authorized connection to Kalshi's V2 trade API, handling automatic reconnections and message routing.
- **`orderbook_manager.py`**: Subscribes to L2 orderbook snapshots and deltas over the websocket to maintain a real-time, low-latency local view of the market bids and asks.
- **`inventory_manager.py`**: Tracks your current USD balance and net contract positions. It hydrates the initial state via the REST API upon startup and updates in real-time by listening to websocket `fill` trade execution events.

### 3. Execution & Safety (`execution/`)
- **`order_manager.py`**: Handles placing and cancelling Limit orders asynchronously via Kalshi's REST API, while keeping a crucial local registry of active `client_order_id`s.
- **`kill_switch.py`**: A vital risk-management safety feature. Capable of instantly cancelling all locally tracked active orders. It supports both asynchronous and synchronous emergency cancellation (e.g., if the bot crashes, is interrupted via `Ctrl+C`, or exceeds risk limits) to immediately drop market exposure.

### 4. Trading Strategy (`strategy/`)
- **`market_maker.py`**: Implements a simplified **Avellaneda-Stoikov** algorithmic market-making strategy.
  - Dynamically calculates a theoretical "Mid Price" based on the live orderbook.
  - Evaluates your current contract inventory position to adjust a "Reservation Price" (your true target price) to reduce directional inventory risk, heavily influenced by an adjustable risk-aversion parameter (`gamma`).
  - Continuously places and replaces Bid and Ask limit orders symmetrically around this Reservation Price to capture a minimum profit margin (`min_spread`).

## Testing Suite

All tests are located in the `tests/` directory and are designed to validate specific subsystems of the architecture on the Kalshi Demo environment. 

### `tests/test_ws_stream.py` (Data & Subscriptions)
**Purpose**: Verifies that the core data ingestion pipeline and WebSocket subscriptions work.
**Behavior**: Connects to Kalshi's WebSocket API, subscribes to the orderbook for a random active market, and simultaneously hits the REST API to hydrate your Demo portfolio balance. It spends 5 seconds listening to the live stream, outputting the continuous `Best Bid`, `Best Ask`, and your net position tracking.

### `tests/test_execution.py` (Order Management)
**Purpose**: Verifies that the bot can accurately place, track, and explicitly cancel orders via the REST API.
**Behavior**: Successfully places a dummy limit order (1 "yes" contract) priced at 1 cent (deep out-of-the-money) on a random market. The `OrderManager` captures the local ID. After 3 seconds, it sends a REST API request to fully cancel that specific order, validating the round-trip execution capabilities.

### `tests/test_kill_switch.py` (Emergency Safety)
**Purpose**: Validates the global safety mechanism designed to clear out risk exposure instantly in an emergency.
**Behavior**: Places a 1-cent dummy limit order and registers it locally. The test script then simulates an unexpected software failure by programmatically invoking the async kill switch trigger. The Kill Switch immediately iterates over all tracked active orders and fires asynchronous cancellation API calls, ensuring the account is left flat.

### `tests/test_strategy.py` (The Full Bot Loop)
**Purpose**: A dry-run of the full, integrated market-making bot.
**Behavior**: Selects an active market and successfully boots the `AvellanedaStoikovBot` class. The bot initializes the WebSocket, syncs its REST state, opens subscriptions, and begins its main quoting valuation loop. It is intentionally wired to listen for a manual keyboard interrupt (`Ctrl+C`). When triggered, it successfully fires the synchronous safety shut-down sequence—withdrawing all quotes—before cleanly exiting the process.
