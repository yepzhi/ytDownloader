FROM python:3.10

# Install system dependencies
# Using full image, but ensure ffmpeg is there.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade yt-dlp

COPY . .

# Create a user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
