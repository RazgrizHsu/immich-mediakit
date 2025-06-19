

set -e

IMAGE_NAME="razgrizhsu/immich-mediakit"

SCRIPT_DIR="$(dirname "$0")"
if [ ! -f "$SCRIPT_DIR/pyproject.toml" ]; then
  echo "Error: pyproject.toml not found in $SCRIPT_DIR"
  exit 1
fi
VERSION=$(grep '^version = ' "$SCRIPT_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
if [ -z "$VERSION" ]; then
  echo "Warning: Could not read version from pyproject.toml, using 'latest'"
  VERSION="latest"
fi
TAG="${VERSION}"
UPLOAD=false

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

echo "Starting Docker image build process..."

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

echo "Using Docker Buildx builder 'budx'."
docker buildx use budx

PLATFORMS="linux/amd64,linux/arm64/v8"

BUILD_ARGS=(
  "--build-arg" "MKIT_PORT=8086"
  "--build-arg" "MKIT_PORTWS=8087"
  "."
)

if [ "$UPLOAD" = true ]; then
  echo "Building multi-platform Docker images for ${PLATFORMS} and pushing to Docker Hub: ${IMAGE_NAME}:${TAG}"

  docker buildx build \
    --platform "${PLATFORMS}" \
    -t "${IMAGE_NAME}:${TAG}" \
    -t "${IMAGE_NAME}:latest" \
    "${BUILD_ARGS[@]}" \
    --push

  echo "Successfully built and pushed ${IMAGE_NAME}:${TAG} and ${IMAGE_NAME}:latest for multiple platforms."

else
  echo "Building Docker image for current host platform and loading to local Docker daemon (not pushing)."
  echo "To build and push multi-platform images, run with --upload option."

  CURRENT_PLATFORM=$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/amd64/')

  docker buildx build \
    --platform "${CURRENT_PLATFORM}" \
    -t "${IMAGE_NAME}:${TAG}" \
    "${BUILD_ARGS[@]}" \
    --load

  echo "Successfully built and loaded ${IMAGE_NAME}:${TAG} for local testing."
fi

echo "Build process completed."
