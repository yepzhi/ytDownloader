FROM python:3.9

# Standard Python Image (Debian based)

# Install deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Switch back to PyPI for build stability (GitHub direct often fails in restricted builds)
RUN pip install --upgrade yt-dlp

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
