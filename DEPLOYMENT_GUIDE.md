# Deployment Guide

This guide outlines the step-by-step process to verify that the Kalshi Trading Bot is successfully running on the DigitalOcean Droplet and that the local observability stack (Prometheus & Grafana) is correctly receiving its live metrics over the internet.

## 1. Verify the Droplet (The Bot)
If Grafana is showing "No Data", it is likely because the bot is currently turned off. We need to start it up on the server.

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
4. **View live logs:** 
   ```bash
   docker compose logs -f bot
   ```
5. **Restart the bot (if needed):** 
   ```bash
   docker compose restart bot
   ```
6. **Stop the bot:** 
   ```bash
   docker compose down
   ```

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
