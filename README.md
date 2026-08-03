# Kalshi Algorithmic Market Maker Bot

This project is a fully-functional algorithmic **market-making trading bot** built for the Kalshi prediction market platform. Its primary goal is to provide dual-sided liquidity (bids and asks) on Kalshi markets to capture the bid-ask spread while actively managing inventory risk.

## System Architecture

```mermaid
graph TD
    subgraph Local Environment [Local Environment (Monitoring)]
        Grafana[Grafana Dashboard] -->|Visualize Metrics| Prometheus[Prometheus Database]
    end

    subgraph DigitalOcean [DigitalOcean Droplet (Cloud VPS)]
        subgraph DockerContainer [Docker Container: kalshi-bot]
            BotLoop[Avellaneda-Stoikov Bot Loop]
            OrderBook[Orderbook Manager]
            InvManager[Inventory Manager]
            OrderManager[Order Manager]
            KillSwitch[Kill Switch]
            Auth[RSA Cryptographic Auth]
        end
    end

    subgraph External [External Services]
        GHCR[GitHub Container Registry] -->|Deploy Image| DockerContainer
        KalshiWS[Kalshi V2 WebSockets] <-->|Real-time Feed & Fills| OrderBook
        KalshiWS <-->|Fills| InvManager
        OrderManager -->|REST Order Placement/Cancel| KalshiREST[Kalshi V2 REST API]
        KillSwitch -->|Emergency Cancel| KalshiREST
        Prometheus -->|Scrape Metrics: Port 8000| BotLoop
    end

    %% Flow relationships inside the container
    BotLoop -->|Evaluate Risk & Mid Price| OrderBook
    BotLoop -->|Evaluate Exposure| InvManager
    BotLoop -->|Send Quotes| OrderManager
    BotLoop -.->|Interrupt / Safety Shutdown| KillSwitch
    OrderManager -.->|Register Active IDs| KillSwitch
    Auth -.->|Sign Requests| OrderManager
    Auth -.->|Authorize Connection| KalshiWS
```

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

