#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

# Check if the monitoring namespace exists, and create it only if it does not exist
if ! kubectl get namespace monitoring > /dev/null 2>&1; then
    echo "Creating 'monitoring' namespace..."
    kubectl create namespace monitoring
else
    echo "'monitoring' namespace already exists."
fi

# Delete any existing Prometheus pods to ensure fresh deployment
echo "Deleting existing Prometheus pods in the 'monitoring' namespace..."
kubectl delete pod -l app=prometheus -n monitoring --ignore-not-found

# Apply the ConfigMap, Deployment, and Service YAML files for Prometheus
echo "Applying Prometheus ConfigMap and Deployment..."
kubectl apply -f prometheus-configmap.yaml
kubectl apply -f prometheus-deployment.yaml

# Check the status of the pods in the 'monitoring' namespace
echo "Checking the status of Prometheus pods..."
kubectl get pods -n monitoring
