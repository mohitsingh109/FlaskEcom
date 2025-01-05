#!/bin/bash

cd "$(dirname "$0")" || exit

# Check if the monitoring namespace exists, and create it only if it does not exist
if ! kubectl get namespace monitoring > /dev/null 2>&1; then
    echo "Creating 'monitoring' namespace..."
    kubectl create namespace monitoring
else
    echo "'monitoring' namespace already exists."
fi

# Apply Grafana Deployment YAML
kubectl apply -f grafana-deployment.yaml

# Verify if the Grafana deployment was successful
kubectl get pods -n monitoring -l app=grafana
