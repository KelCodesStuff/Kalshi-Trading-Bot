FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies if required by any lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the setup file to install dependencies via pip
COPY setup.py /app/

# Upgrade pip and install the app's requirements
RUN pip install --upgrade pip
RUN pip install -e .

# Copy the actual application files
COPY . /app/

# Expose port 8000 for Prometheus metrics
EXPOSE 8000

# Run the strategy by default
ENTRYPOINT ["python", "tests/test_strategy.py"]
