# Project Setup Guide

To properly run your market-making bot 24/7 without worrying about your laptop going to sleep, losing internet, or running out of power, deploying it to a small remote server is highly recommended. 

This guide details how to spin up a basic **$6/month DigitalOcean Droplet** and run the bot permanently in the background using `tmux`.

## Step 1: Create the Droplet

1. Log into your [DigitalOcean Dashboard](https://cloud.digitalocean.com/).
2. Click **Create** > **Droplets**.
3. **Region**: Choose the region closest to Kalshi's servers. Kalshi's API is hosted in **AWS us-east-1 (N. Virginia/NYC)**. Choosing **New York 1 or 3** will likely give you the lowest possible websocket latency.
4. **OS Image**: Select **Ubuntu** (24.04 LTS or latest).
5. **Droplet Type**: Basic.
6. **CPU Options**: Regular ($6/month plan with 1GB RAM is plenty for a single Python bot script).
7. **Authentication**: Choose **SSH Key** (highly recommended for security) or set a strong Password. You'll use this to log into the server.
8. Click **Create Droplet**. 
9. Once created, copy the Droplet's public **IPv4 Address**.

## Step 2: Log into the Server

Open your laptop's terminal and log into the remote server as the `root` user using the IP address you copied:

```bash
ssh root@YOUR_DROPLET_IP
# (Type "yes" if prompted to accept the fingerprint, and enter your password if you didn't use an SSH key)
```

## Step 3: Install Core Dependencies

Once inside the remote server, update the system packages and install Python, pip, a virtual environment manager, Git, and `tmux`:

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install python3 python3-pip python3-venv git tmux -y
```

## Step 4: Transfer Your Code

The cleanest way to get your code onto the server is via GitHub (by pushing your code from your laptop and `git clone`ing it on the Droplet). 

Alternatively, if you haven't set up GitHub for this project yet, you can push the folder directly from your laptop to the remote server using `scp`. 

**Option A (SCP Transfer)** - *Run this on your LAPTOP terminal, not the server:*
```bash
scp -r /Users/kelreid/Projects/Kalshi-Trading-Bot root@YOUR_DROPLET_IP:~/
```

## Step 5: Configure the Bot Environment

Log back into your Droplet (if you logged out) and navigate to the newly copied bot folder:

```bash
cd ~/Kalshi-Trading-Bot
```

Set up your Python virtual environment and install the required packages:

```bash
python3 -m venv .venv
source .venv/bin/activate

# Install the dependencies your bot relies on
pip install websockets requests python-dotenv cryptography certifi
```

Create your configuration environment file:

```bash
cp .env.example .env
nano .env # (This opens a built-in text editor)
```
*In the nano text editor, specify your `KALSHI_API_KEY`, your `ALERT_WEBHOOK_URL`, and adjust your `RISK_GAMMA` or `TARGET_TICKER` parameters.* 
*Press `Ctrl+O`, `Enter`, then `Ctrl+X` to save and exit.*

**(Crucial Step):** You must securely transfer your `.pem` private key file to the server (you can use `scp` the same way you copied the folder). DO NOT leave Demo credentials on a server pointing to Prod without understanding the risks.

## Step 6: Start the Bot in the Background (`tmux`)

If you simply ran `python main.py` right now, the bot would immediately die as soon as you close your terminal window or your laptop goes to sleep. To keep it running forever persistently, we use a terminal multiplexer called **tmux**.

1. **Start a new background session**:
```bash
tmux new -s kalshi_bot
```
2. **Activate the environment and run the bot**:
```bash
source .venv/bin/activate
python main.py
```
3. **Detach and leave it running forever**:
Once you see the bot successfully printing logs ("State hydrated. Beginning quoting loop."), you can **"detach"** from the tmux session. 

Press **`Ctrl+B`**, physically release both keys, then press **`D`**.

You will be dropped back to your normal server terminal, but the bot is still running invisibly in the background. You can now safely type `exit` to close your SSH connection and shut your laptop. **The bot will continue trading 24/7.**

## Managing the Deployed Bot

Whenever you want to see what the bot is doing, deploy new code, or adjust the settings later on:

1. SSH back into your Droplet: `ssh root@YOUR_DROPLET_IP`
2. Reattach to the hidden session to view the live logs: 
```bash
tmux attach -t kalshi_bot
```
3. To stop trading and kill the bot, press `Ctrl+C` (This invokes the safety Kill Switch, instantly cancelling your open quotes on the Kalshi exchange).
4. You can edit `.env` or `git pull` new changes, then run `python main.py` again.
5. To leave it running again, press `Ctrl+B`, release, then press `D`.
