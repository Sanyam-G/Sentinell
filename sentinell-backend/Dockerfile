FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose API port
EXPOSE 8001

# Set DOCKER_HOST to explicit unix socket
ENV DOCKER_HOST=unix:///var/run/docker.sock

# Run the observer
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
