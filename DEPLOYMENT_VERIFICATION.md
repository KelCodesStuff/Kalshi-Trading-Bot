# Deployment Verification Guide

This document outlines the step-by-step process to verify that the Kalshi Trading Bot, the DigitalOcean Droplet server, and the local Grafana monitoring stack are all running correctly and communicating with each other.

## 1. Verify the DigitalOcean Droplet is Alive

### Method A: DigitalOcean Dashboard (No Terminal Required)
1. Log in to your [DigitalOcean Dashboard](https://cloud.digitalocean.com/).
2. Click on your active Droplet (e.g., `kalshi-bot-prod`).
3. Look at the **Graphs** on the Droplet's overview page:
   - **CPU Usage:** You should see a steady heartbeat line of low CPU usage (e.g., 2-5%) rather than a flat 0%.
   - **Bandwidth:** You should see constant inbound and outbound network traffic as the bot streams websocket data from Kalshi.

### Method B: Droplet Terminal (tmux logs)
Check the raw logs of the trading bot to ensure it hasn't crashed.

1. SSH into the Droplet using your Mac's terminal:
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```
2. Attach to the persistent background session that holds the running bot:
   ```bash
   tmux attach -t kalshi
   ```
3. **What to look for:** You should see scrolling logs indicating a successful connection and live operation, such as:
   ```text
   INFO - WebSocket Connected. Hydrating state...
   INFO - State hydrated. Beginning quoting loop.
   ```
4. **Important:** When you are done observing, do **NOT** press `Ctrl + C` (that will terminate the bot). Instead, **safely detach** from the session so it continues running in the background:
   - Press `Ctrl + B`
   - Release both keys, then press `D`

## 2. Verify Prometheus is Scraping the Droplet
Prometheus is responsible for reaching out to the DigitalOcean Droplet every two seconds to pull the latest algorithmic performance metrics.

1. Ensure your monitoring containers are running locally on your Mac:
   ```bash
   docker compose up -d
   ```
2. Open your web browser and navigate to the Prometheus Targets page:
   [http://localhost:9090/targets](http://localhost:9090/targets)
3. Locate the `kalshi-bot` endpoint target in the list.
4. **What to look for:** Look at the **State** column. If it displays a green **UP**, Prometheus is successfully retrieving data from `<YOUR_DROPLET_IP>:8000`. If it says **DOWN**, ensure the bot is actually running on the Droplet and that the IP address in your Mac's `prometheus.yml` file exactly matches your Droplet's public IP address.

## 3. Verify Grafana is Displaying Live Data
Grafana translates the raw data from Prometheus into the visual trading cockpit.

1. Open your web browser and navigate to the Grafana interface:
   [http://localhost:3000](http://localhost:3000)
2. In the left-hand menu, navigate to **Dashboards** and select your **Kalshi Market Maker** dashboard.
3. **What to look for:**
   - **API Latency:** This graph (bottom left) should show a constant, real-time stream of dots representing the millisecond response time from Kalshi's API to your Droplet.
   - **Profit & Loss / Inventory Risk:** These graphs (right side) will continuously track your net position and current PnL on the active market.
   - **"No Data" Panels:** It is completely normal for the "Orders Placed", "Total Buy", and "Total Sell" contract panels to display "No Data" until the bot places its very first trade. These specific prometheus metrics are dynamically generated only upon the first transaction.

If all three layers show activity, your production market-making infrastructure is 100% interconnected and fully operational!
