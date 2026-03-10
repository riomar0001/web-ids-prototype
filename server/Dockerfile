FROM python:3.12-slim

# Scapy requires libpcap for packet sniffing
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpcap-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /ids/server

COPY docker-requirements.txt .
RUN pip install --no-cache-dir -r docker-requirements.txt

# Build context is server/ itself, copy everything into /ids/server/
COPY . .

WORKDIR /ids

EXPOSE 8000

# NET_RAW capability is required for Scapy packet capture.
# Run with: docker run --cap-add=NET_RAW ...
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
