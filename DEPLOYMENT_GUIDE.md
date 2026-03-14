# Deployment Guide

This guide outlines the step-by-step process to verify that the Kalshi Trading Bot is successfully running on the DigitalOcean Droplet and that the local observability stack (Prometheus & Grafana) is correctly receiving its live metrics over the internet.

## 1. Verify the Droplet (The Bot)
If Grafana is showing "No Data", it is likely because the bot is currently turned off. We need to start it up on the server.

1. **SSH into your droplet:** 
   ```bash
   ssh root@159.65.229.254
   ```
2. **Connect to your background session:** 
   ```bash
   tmux attach -t kalshi
   ```
   *(If it says session not found, create a new one: `tmux new-session -s kalshi`)*
3. **Navigate to the folder:** 
   ```bash
   cd ~/Kalshi-Trading-Bot
   ```
4. **Start the bot:** 
   ```bash
   python tests/test_strategy.py
   ```
5. **Detach:** Wait a few seconds to verify it connects to the WebSocket and begins the "quoting loop". Once it does, press `Ctrl+B`, let go, and press `D` to detach and leave it running in the background!
6. **Stop the bot:** If you ever need to stop the bot, re-attach to the session (`tmux attach -t kalshi`) and press `Ctrl+C`. This safely triggers the synchronous kill switch, cancelling all of your active orders before shutting the bot down.
## 2. Verify Prometheus (The Database)
Now that the bot is running on the Droplet, your local Prometheus database (running via Docker on your Mac) should be successfully scraping it over the internet every 2 seconds.

1. Open your Mac's browser and go to: [http://localhost:9090/targets](http://localhost:9090/targets)
2. You should see `kalshi-bot` listed there with the Droplet's IP address.
3. The "State" badge should say **UP** in green. *(If it says DOWN, double-check that the bot hasn't crashed on the Droplet).*

## 3. Verify Grafana (The Dashboard)
Finally, check the beautiful UI!

1. Open your Mac's browser and go to: [http://localhost:3000](http://localhost:3000)
2. Open your "Kalshi Market Maker" dashboard.
3. Since the bot is actively running on the server, you should see the `bot_inventory_net_position` graph drawing live data points, the `orders_placed_total` counters climbing, and the latency histogram populating!
