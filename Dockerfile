FROM python:3.9-slim

# Install system dependencies (FFmpeg is required for yt-dlp audio)
# ca-certificates needed for HTTPS/SSL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Upgrade yt-dlp to ensure latest extractors
RUN pip install --upgrade yt-dlp

COPY . .

# Create a user to avoid running as root (Good practice for HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
