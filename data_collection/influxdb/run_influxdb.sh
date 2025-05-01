#!/bin/bash
COMPOSE_FILE="docker-compose.yaml"

echo "Checking docker status..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi
echo "  Docker OK"

echo "Checking docker compose status..."
if ! docker compose version &> /dev/null; then
    echo "Error: Docker compose is not installed"
    exit 1
fi
echo "  Docker compose OK"
echo ""

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: $COMPOSE_FILE does not exist in this directory"
    exit 1
fi

echo "Starting influxDB container..."
docker compose up -d

echo ""
echo "InfluxDB container is running on port 8086"
echo "password, username, organisation, bucket and admin token are listed in the config.env file"
echo ""
echo "Container by default listens on 0.0.0.0 (all interfaces)"
echo "IP addresses of this machine's interfaces:"
ip -o -4 addr show | awk '{print $2 ": " $4}'

echo ""
echo "Docker status:"
docker ps