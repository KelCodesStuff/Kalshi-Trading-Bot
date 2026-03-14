# Grafana Setup Guide

This repository comes pre-configured with a Prometheus metrics exposure framework built into the Python trading bot. A `docker-compose.yml` and `prometheus.yml` file is provided to easily spin up a local observability stack.

## 1. Starting the Stack
Ensure Docker Desktop is running on your machine, then execute:
```bash
docker compose up -d
```
This command launches two background services:
1. **Prometheus (Port 9090)**: A time-series database configured to continually "scrape" (poll) the python bot at `host.docker.internal:8000` for metrics every 2 seconds.
2. **Grafana (Port 3000)**: The UI dashboarding tool.

## 2. Connecting Grafana to Prometheus
1. Wait for the docker containers to spin up, then open a browser and go to `http://localhost:3000`.
2. Login with the default credentials (`admin` / `admin`).
3. Under Connections -> Data Sources, click **Add Data Source** and select Prometheus.
4. Set the HTTP URL to: `http://prometheus:9090`.
5. Scroll down to click **Save & Test**.

## 3. Recommended "Kalshi Market Maker" Panels
When you create a new Dashboard in Grafana, here are the recommended queries to use for the standard "Cockpit" view while the bot is active. 

*Ensure the query editor is in "Code" mode and the time range in the top right is set to "Last 5 minutes" or "Last 15 minutes" to see the active lines.*

### 1. Total Orders Placed
A total counter tracking how many limit orders the algorithm successfully evaluated, fired to Kalshi, and received a `201 Created` confirmation.
* **Visualization Form:** Stat (Single large number)
* **Query:** `sum(orders_placed_total)`

### 2. Total Buy Contracts
A discrete counter tracking only the successful buy limit orders.
* **Visualization Form:** Stat (Single large number)
* **Query:** `sum(orders_placed_total{action="buy"})`

### 3. Total Sell Contracts
A discrete counter tracking only the successful sell limit orders.
* **Visualization Form:** Stat (Single large number)
* **Query:** `sum(orders_placed_total{action="sell"})`

### 4. Profit & Loss (Cents)
Tracks the real-time balance of the bot in cents.
* **Visualization Form:** Time series line graph
* **Query:** `bot_pnl_cents`

### 5. Profit & Loss (USD)
Tracks the real-time balance of the bot in dollars.
* **Visualization Form:** Time series line graph
* **Query:** `bot_pnl_cents / 100`

### 6. Current Inventory Risk (Net YES Contracts)
Displays the net position held on the current active market. A high positive or negative number indicates the bot is heavily exposed to a direction.
* **Visualization Form:** Time series line graph
* **Query:** `bot_inventory_net_position`

### 7. Kalshi API Latency (ms)
Tracks the rolling average roundtrip latency time required to successfully execute a REST API limit order placement or cancellation. Spikes here could lead to adverse market execution.
* **Visualization Form:** Time series
* **Query:** `rate(kalshi_api_latency_seconds_sum[1m]) / rate(kalshi_api_latency_seconds_count[1m]) * 1000`
