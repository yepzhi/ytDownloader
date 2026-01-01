FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (Full Ubuntu Stack)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    git \
    curl \
    wget \
    dnsutils \
    iputils-ping \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Use pip through python3
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Install yt-dlp from Master
RUN python3 -m pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip

COPY . .

# Run as ROOT
EXPOSE 7860

# Diagnostics + App Start
# We check network connectivity (Ping ip) and DNS (Dig) before starting
CMD ["sh", "-c", "echo '--- DIAGNOSTICS ---'; ping -c 2 8.8.8.8 || echo 'PING FAILED'; echo '--- DNS LOOKUP ---'; nslookup www.youtube.com || echo 'NSLOOKUP FAILED'; echo '--- STARTING APP ---'; uvicorn app:app --host 0.0.0.0 --port 7860"]
