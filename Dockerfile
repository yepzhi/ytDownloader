FROM python:3.9

# Standard Python Image (Debian based)
# Run as Root by default

# Install deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
