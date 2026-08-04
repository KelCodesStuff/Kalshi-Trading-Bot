# Deployment Guide

This guide outlines the step-by-step process to verify that the Kalshi Trading Bot is successfully running on the DigitalOcean Droplet and that telemetry is correctly flowing through Grafana Alloy to your Grafana Cloud account.

## 1. Verify the Droplet (The Bot)

The bot runs inside a background Docker container on your Droplet.

1. **SSH into your droplet:**
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```
2. **Navigate to the deployment folder:**
   ```bash
   cd ~/Kalshi-Trading-Bot
   ```
3. **Check the bot status:**
   ```bash
   docker compose ps
   ```
   *(Verify that the status is listed as "Up").*
4. **View live execution logs:**
   ```bash
   docker compose logs -f bot
   ```
5. **Restart the bot:**
   ```bash
   docker compose restart bot
   ```
6. **Stop the bot:**
   ```bash
   docker compose down
   ```

## 2. Verify Grafana Alloy (The Telemetry Collector)

Grafana Alloy runs as a background service on the Droplet host system, scraping the bot's exposed port 8000 and pushing data to the cloud.

1. **Check Alloy service status:**
   ```bash
   sudo systemctl status alloy
   ```
   *(Confirm it shows "active (running)" and the logs display "{^_^} Alloy is running").*
2. **View recent Alloy logs:**
   ```bash
   journalctl -u alloy.service -n 50 --no-pager
   ```
   *(Verify there are no "authentication failed" or "non-recoverable error" messages).*

## 3. Verify Grafana Cloud (The Dashboard)

Once both the bot and Alloy services are running on the server, you can view the metrics dashboard from any device:

1. Open your web browser and navigate to your Grafana instance (e.g., `https://<your_subdomain>.grafana.net`).
2. Log into your account and open the **Kalshi Market Maker** dashboard.
3. Confirm that the data series are actively plotting points for:
   * **Profit & Loss**
   * **Current Inventory Risk**
   * **API Latency**
   * **Total Orders Placed** (once the bot executes its first quote placements)
