#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Execute PostgreSQL setup script
echo "Setting up PostgreSQL..."
bash postgres/setup_postgres.sh

# Execute Grafana setup script
echo "Setting up Grafana..."
bash grafana/steup_grafana.sh

# Execute Prometheus setup script
echo "Setting up Prometheus..."
bash prometheus/setup_prometheus.sh

echo "Platform deployment completed successfully!"
