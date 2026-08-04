# Pre-Production Checklist: Trading with Real Money

This guide outlines the essential steps and milestones you must achieve before migrating the Kalshi Trading Bot from the **Demo** environment to the **Production** environment with real capital.

## Phase 1: The Survival Test (1-2 Weeks on Demo)
*Goal: Prove the bot is mechanically stable and safe from catastrophic failures.*

- [ ] **Zero Crashes:** The bot must run continuously on the DigitalOcean Droplet for at least 7 consecutive days without the Python process crashing or running out of memory.
- [ ] **Zero Orphaned Orders:** Manually trigger the Kill Switch (run `docker compose down` on the Droplet) during an active trading session. Verify via the Kalshi UI that absolutely zero open orders were left behind.
- [ ] **State Recovery Verification:** Simulate a sudden container failure by running `docker kill kalshi-bot` to forcefully terminate the process. Restart the bot and verify its initialization sequence correctly finds and cancels the old resting orders before quoting again.
- [ ] **Clean Rate Limits:** Monitor your Grafana dashboard. The `order_errors_total` panel should remain at `0`. If you consistently hit `429 Too Many Requests`, your algorithm is too aggressive and must be tuned down before Production.
- [ ] **Connection Stability:** Ensure the websocket connection successfully auto-reconnects and re-hydrates state if Kalshi drops the connection.

## Phase 2: The Mechanics Test (Demo)
*Goal: Prove the algorithm correctly applies risk math and spread logic.*

- [ ] **Spread Maintenance:** Monitor the bot's Bid/Ask spread in the logs or UI. With `MIN_SPREAD=4`, confirm it never accidentally crosses the spread or quotes a margin smaller than 4 cents.
- [ ] **Inventory Risk Skewing:** Pick a market and let the bot accumulate contracts on one side (e.g., holding 20 YES). Observe its quoting behavior. It must aggressively lower its Bid price (to avoid buying more) and lower its Ask price (to incentivize selling off the inventory). If it doesn't, increase `RISK_GAMMA`.
- [ ] **Tick Size Compliance:** Verify the bot never attempts to quote at invalid price increments (e.g., trying to place an order at 50.5 cents). Kalshi requires whole cents (1c to 99c).

## Phase 3: "Penny Prod" Trading (1-2 Weeks on Prod)
*Goal: Expose the bot to real human traders with extremely strict training wheels to limit financial risk.*

- [ ] Create Production API Keys on the live Kalshi website.
- [ ] Update your Droplet's `~/Kalshi-Trading-Bot/.env` file:
    - Set `KALSHI_ENV=prod`
    - Replace the Demo API keys with the Production keys
    - Provide the path to the production `.pem` key file
- [ ] Apply **Extreme Risk Limits** in `.env`:
    - `ORDER_SIZE=1` (Trade exactly 1 contract at a time)
    - `MIN_SPREAD=6` (Require a massive 6-cent theoretical profit margin)
- [ ] Start the bot on a high-liquidity market (e.g., S&P 500 Daily, major temperature markets).

*Note: You may lose a few dollars during this phase. Because your `ORDER_SIZE` is 1, any mistakes will cost pennies. Your objective is to observe if human traders are "picking you off" before your bot can update its prices.*

## Phase 4: Tuning for Profit (Continuous)
*Goal: Slowly increase size and competitiveness once the bot proves it functions correctly against real retail order flow.*

- [ ] Analyze the Grafana `kalshi_api_latency_seconds` data. If REST API latency is consistently >50ms, the bot may be too slow to cancel orders during news events.
- [ ] Gradually decrease `MIN_SPREAD` to become more competitive in the orderbook.
- [ ] Gradually increase `ORDER_SIZE` only after achieving a consistently positive win-rate on a 1-contract basis.
- [ ] Continuously tune `RISK_GAMMA` to balance how quickly the bot dumps inventory versus how much directional risk it is allowed to hold.
