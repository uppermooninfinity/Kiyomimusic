FROM nikolaik/python-nodejs:python3.10-nodejs19

# Set working directory first
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

# Upgrade pip & install deps
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

# Now copy full project
COPY . .

# Run your bot
CMD ["python3", "-m", "Oneforall"]
