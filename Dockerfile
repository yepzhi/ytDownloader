FROM python:3.10

# Install system dependencies
# ca-certificates is CRITICAL for HTTPS/DNS over TLS etc.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    dnsutils \
    iputils-ping \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install yt-dlp from Master
RUN pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip

COPY . .

# Run as ROOT
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
