FROM python:3.11-slim

# docker.io provides the `docker` CLI binary, which the load balancer
# uses (via the mounted /var/run/docker.sock) to spawn/remove server
# containers on the host's Docker daemon.
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
