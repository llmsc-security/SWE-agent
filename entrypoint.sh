#!/bin/bash
# Entrypoint script for SWE-agent API server
# Starts the Flask API server on port 11400 (mapped port)

set -e

echo "Starting SWE-agent API server..."

# Run the API server on port 11400 (mapped port)
exec python -m sweagent.api.server --port 11400
