# Use a more compatible base image
FROM python:3.13.3-slim-bookworm@sha256:21e39cf1815802d4c6f89a0d3a166cc67ce58f95b6d1639e68a394c99310d2e5

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5005

# Run the application with Gunicorn
CMD ["sh", "-c", "gunicorn --log-level debug -b 0.0.0.0:5005 --workers 5 --timeout 240 --worker-class gevent --certfile=$SSL_CERT_FILE --keyfile=$SSL_KEY_FILE app:app"]