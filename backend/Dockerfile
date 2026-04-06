FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js for yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    openssl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy application
COPY . .

COPY yt-dlp.conf /etc/yt-dlp.conf

# Create downloads directory
RUN mkdir -p downloads

# Set environment variables for yt-dlp to find Node.js
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin"
ENV NODE_PATH="/usr/lib/node_modules"

RUN pip install --upgrade yt-dlp
# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
