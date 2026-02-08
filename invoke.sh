#!/bin/bash
# Build and run SWE-agent Docker container
# Maps port 11400 on host to port 8000 in container (API default)

set -e

# Configuration
CONTAINER_NAME="swe-agent-api"
IMAGE_NAME="swe-agent:latest"
HOST_PORT=11400
CONTAINER_PORT=8000

# Build the Docker image
echo "Building Docker image..."
docker build -t "$IMAGE_NAME" .

# Run the container with port mapping
echo "Starting container '$CONTAINER_NAME'..."
docker run --rm \
    --name "$CONTAINER_NAME" \
    -p "$HOST_PORT:$CONTAINER_PORT" \
    -e PORT=$CONTAINER_PORT \
    -v "$(pwd)":/app \
    "$IMAGE_NAME"
