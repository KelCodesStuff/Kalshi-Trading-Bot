# Project Setup Guide: Docker and CI/CD Deployment

This guide details how to configure a remote DigitalOcean Droplet and set up the automated GitHub Actions deployment pipeline for the Kalshi Trading Bot. Using this setup, every push to the `main` branch builds a new Docker container and deploys it automatically to your server.

## Step 1: Create the Droplet

1. Log into your DigitalOcean Dashboard.
2. Click **Create** > **Droplets**.
3. **Region**: Choose **New York** (NY1 or NY3). Kalshi's API is hosted in AWS us-east-1 (N. Virginia/NYC area), so New York hosting provides the lowest possible network latency.
4. **OS Image**: Select **Ubuntu** (24.04 LTS or latest).
5. **Droplet Type**: Basic.
6. **CPU Options**: Regular ($6/month plan with 1GB RAM is sufficient).
7. **Authentication**: Choose **SSH Key** (highly recommended for security). You will need the private key associated with this SSH key to authenticate GitHub Actions.
8. Click **Create Droplet** and copy the public IPv4 Address of the Droplet.

## Step 2: Install Docker on the Droplet

Log into your Droplet console via SSH:

```bash
ssh root@YOUR_DROPLET_IP
```

Install Docker on the server using the official Docker installation script (which automatically resolves package repository conflicts):

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Verify that the Docker service is running:

```bash
sudo systemctl status docker
```

Create the directory where your Docker Compose configuration will reside:

```bash
mkdir -p ~/Kalshi-Trading-Bot
```

## Step 3: Configure GitHub Secrets

For GitHub Actions to deploy to your Droplet, you must configure four repository secrets. 

1. Go to your repository on GitHub.
2. Click **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.
3. Add the following secrets:

* **`DROPLET_IP`**: The public IPv4 address of your Droplet.
* **`SSH_USERNAME`**: Set this to `root`.
* **`SSH_PRIVATE_KEY`**: Paste the entire contents of your private SSH key (usually `~/.ssh/id_rsa` or similar) that matches the public key registered on the Droplet.
* **`PAT_GHCR`**: A GitHub Personal Access Token (classic) with `read:packages` and `write:packages` permissions. This allows the Droplet to pull the private container image from the GitHub Container Registry.

## Step 4: Deploy via Git Push

Once the secrets are in place, trigger the deployment pipeline by pushing your code to the `main` branch:

```bash
git add .
git commit -m "Configure CI/CD deployment"
git push origin main
```

Monitor the progress under the **Actions** tab of your GitHub repository. The workflow will build the Docker container, push it to the GitHub Container Registry, copy `docker-compose.yml` to the Droplet, and run the container in the background.

## Step 5: Verify the Deployment

SSH back into your Droplet to check that the container is running and to view the live logs:

1. **Check container status:**
   ```bash
   cd ~/Kalshi-Trading-Bot
   docker compose ps
   ```
2. **View live execution logs:**
   ```bash
   docker compose logs -f bot
   ```
3. **Emergency kill-switch (cancel orders and exit):**
   ```bash
   docker kill --signal=SIGINT kalshi-bot
   ```
