FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install yt-dlp from Master
RUN pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.zip

COPY . .

# Run as ROOT to avoid socket/permission issues
# RUN useradd -m -u 1000 user
# USER user
# ENV HOME=/home/user \
#     PATH=/home/user/.local/bin:$PATH

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
