# Grafana Setup Guide

This repository comes pre-configured with a Prometheus metrics exposure framework built into the Python trading bot.

We offer an observability architecture that pushes metrics directly to Grafana Cloud.

## 1. Grafana Cloud Setup

This approach uses [Grafana Alloy](https://grafana.com/docs/alloy/latest/), a lightweight telemetry collector, to scrape metrics from the bot and push them directly to your Grafana Cloud account. If your bot runs on a cloud server (like DigitalOcean), you install Alloy there, meaning your laptop doesn't need to stay awake to view metrics.

### Step 1: Install Grafana Alloy on the Bot Server

If your bot is running on a DigitalOcean droplet (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana-alloy
```

### Step 2: Configure Alloy

1. Copy the provided `alloy.config/config.alloy` to your server (e.g., `/etc/alloy/config.alloy`).
2. Set your Grafana Cloud credentials as environment variables on your server:
   ```bash
   export GRAFANA_CLOUD_PROMETHEUS_URL="https://prometheus-us-central1.grafana.net/api/prom/push"
   export GRAFANA_CLOUD_USERNAME="<your_username_id>"
   export GRAFANA_CLOUD_API_KEY="<your_api_key>"
   ```
   *(Note: You can also hardcode these into the `config.alloy` file if preferred, though env variables are safer).*

3. Run the Alloy service:
   ```bash
   alloy run /etc/alloy/config.alloy
   ```
   *(Or restart the systemd service if running as a daemon: `sudo systemctl restart grafana-alloy.service`)*

### Step 3: View Dashboards

Login to your Grafana Cloud instance. You can now build the recommended dashboard panels (see Section 2 below) directly in the cloud. They will populate automatically.

---

## 2. Recommended "Kalshi Market Maker" Panels
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
