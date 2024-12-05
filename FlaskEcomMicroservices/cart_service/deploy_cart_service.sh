#!/bin/bash

# Set variables
IMAGE_NAME="cart_service:latest"
DEPLOYMENT_FILE="k8s/cart-service-deployment.yaml"

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
