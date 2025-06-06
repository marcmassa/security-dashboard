#!/bin/bash

# Deploy Security Dashboard to Google Kubernetes Engine
# Usage: ./scripts/deploy-gke.sh PROJECT_ID CLUSTER_NAME ZONE [IMAGE_TAG]

set -e

if [ -z "$3" ]; then
    echo "Usage: $0 PROJECT_ID CLUSTER_NAME ZONE [IMAGE_TAG]"
    echo "Example: $0 my-gcp-project security-cluster us-central1-a latest"
    exit 1
fi

PROJECT_ID=$1
CLUSTER_NAME=$2
ZONE=$3
IMAGE_TAG=${4:-latest}

echo "Setting up GKE deployment for Security Dashboard..."

# Set gcloud project
gcloud config set project ${PROJECT_ID}

# Get GKE credentials
echo "Getting GKE credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE}

# Update deployment image
echo "Updating deployment image..."
sed -i "s|gcr.io/PROJECT_ID/security-dashboard:latest|gcr.io/${PROJECT_ID}/security-dashboard:${IMAGE_TAG}|g" k8s/deployment.yaml

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configuration and secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n security-dashboard --timeout=300s

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for application to be ready
echo "Waiting for application to be ready..."
kubectl wait --for=condition=ready pod -l app=security-dashboard -n security-dashboard --timeout=300s

# Apply HPA
kubectl apply -f k8s/hpa.yaml

# Apply Ingress (optional)
echo "Do you want to apply Ingress? Make sure to update the domain in k8s/ingress.yaml first."
read -p "Apply Ingress? (y/N): " apply_ingress
if [[ $apply_ingress =~ ^[Yy]$ ]]; then
    kubectl apply -f k8s/ingress.yaml
fi

echo "Deployment completed!"
echo ""
echo "Check deployment status:"
echo "kubectl get pods -n security-dashboard"
echo ""
echo "Get service URL:"
echo "kubectl get service security-dashboard-nodeport -n security-dashboard"
echo ""
echo "Port forward for local testing:"
echo "kubectl port-forward service/security-dashboard-service 8080:80 -n security-dashboard"