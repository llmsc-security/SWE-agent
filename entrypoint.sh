#!/bin/bash
# Entrypoint script for SWE-agent API server
# Starts the Flask API server on port 8000 (container internal)

set -e

echo "Starting SWE-agent API server..."

# Run the API server on port 8000 (container port)
exec python -m sweagent.api.server --port 8000
