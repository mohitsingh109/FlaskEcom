#!/bin/bash

# Set variables
IMAGE_NAME="auth_service:latest"
DEPLOYMENT_FILE="k8s/auth-service-deployment.yaml"

# Check if the deployment exists before attempting to delete it
if kubectl get deployment auth-service > /dev/null 2>&1; then
  echo "Deleting existing deployment: auth-service"
  kubectl delete deployment auth-service
else
  echo "Deployment 'auth-service' does not exist. Skipping deletion."
fi

# Build Docker image using Minikube
echo "Building Docker image: $IMAGE_NAME"
minikube image build -t $IMAGE_NAME .
if [ $? -ne 0 ]; then
  echo "Error: Failed to build Docker image."
  exit 1
fi

# Apply Kubernetes deployment
echo "Applying Kubernetes deployment from $DEPLOYMENT_FILE"
kubectl apply -f $DEPLOYMENT_FILE
if [ $? -ne 0 ]; then
  echo "Error: Failed to apply Kubernetes deployment."
  exit 1
fi

echo "Deployment successful."
