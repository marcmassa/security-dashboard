#!/bin/bash

# Build and push Docker image to Google Container Registry
# Usage: ./scripts/build-and-push.sh PROJECT_ID [TAG]

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 PROJECT_ID [TAG]"
    echo "Example: $0 my-gcp-project latest"
    exit 1
fi

PROJECT_ID=$1
TAG=${2:-latest}
IMAGE_NAME="gcr.io/${PROJECT_ID}/security-dashboard"

echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:${TAG} .

echo "Configuring Docker to use gcloud as a credential helper..."
gcloud auth configure-docker

echo "Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:${TAG}

echo "Image pushed successfully: ${IMAGE_NAME}:${TAG}"
echo "Update k8s/deployment.yaml with this image URL before deploying"