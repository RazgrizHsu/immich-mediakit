#!/bin/bash

set -e

IMAGE_NAME="razgrizhsu/immich-mediakit"

SCRIPT_DIR="$(dirname "$0")"
if [ ! -f "$SCRIPT_DIR/pyproject.toml" ]; then
  echo "Error: pyproject.toml not found"
  exit 1
fi
VERSION=$(grep '^version = ' "$SCRIPT_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
if [ -z "$VERSION" ]; then
  echo "Warning: Could not read version from pyproject.toml, using 'latest'"
  VERSION="latest"
fi
TAG="${VERSION}"
UPLOAD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --upload)
      UPLOAD=true
      shift
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--upload] [--tag TAG]"
      exit 1
      ;;
  esac
done

echo "Building Docker image: ${IMAGE_NAME}:${TAG}"

cd "$(dirname "$0")"

if [ ! -f "requirements.txt" ]; then
  echo "Error: requirements.txt not found"
  exit 1
fi

if [ ! -f "Dockerfile" ]; then
  echo "Error: Dockerfile not found"
  exit 1
fi

if [ ! -d "src" ]; then
  echo "Error: src directory not found"
  exit 1
fi

docker build \
  --tag "${IMAGE_NAME}:${TAG}" \
  --build-arg MKIT_PORT=8086 \
  --build-arg MIKT_PORTWS=8087 \
  .

echo "Successfully built ${IMAGE_NAME}:${TAG}"

if [ "$UPLOAD" = true ]; then
  echo "Uploading to Docker Hub..."

  echo "Pushing ${IMAGE_NAME}:${TAG} to Docker Hub..."
  docker push "${IMAGE_NAME}:${TAG}"

  if [ "$TAG" != "latest" ]; then
    echo "Tagging and pushing as latest..."
    docker tag "${IMAGE_NAME}:${TAG}" "${IMAGE_NAME}:latest"
    docker push "${IMAGE_NAME}:latest"
  fi

  echo "Successfully pushed ${IMAGE_NAME}:${TAG}"
else
  echo "To upload: $0 --upload"
fi
