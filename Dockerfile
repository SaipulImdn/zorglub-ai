# Dockerfile for zorglub-ai
FROM python:3.12-slim

# --- Version ARG and LABEL ---
ARG ZORGLUB_VERSION
LABEL zorglub.version=${ZORGLUB_VERSION}

# Set workdir
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Get version from version.txt
RUN VERSION=$(cat version.txt | tr -d ' \t\n\r') && \
    VERSION=${VERSION#version=} && \
    if [ -z "$VERSION" ]; then \
      echo "ERROR: version.txt is empty or invalid!" && exit 1; \
    fi && \
    echo "version=$VERSION" >> $GITHUB_OUTPUT

# Expose port if needed (e.g., for API)
# EXPOSE 8000

# Default command
CMD ["python", "app.py"]
