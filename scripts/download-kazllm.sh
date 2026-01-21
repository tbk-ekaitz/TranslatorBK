#!/bin/bash

# Script to download KazLLM-8B GGUF model for llama.cpp
# This script downloads the model into the Docker volume

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "KazLLM-8B Model Downloader"
echo "==========================================${NC}"
echo ""

# Model information
MODEL_NAME="llama-3.1-kazllm-1.0-8b-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B-GGUF4/resolve/main/${MODEL_NAME}"
VOLUME_NAME="translatorbk_kazllm_models"

echo -e "${YELLOW}Model:${NC} ${MODEL_NAME}"
echo -e "${YELLOW}Size:${NC} ~5GB (Q4_K_M quantization)"
echo -e "${YELLOW}Source:${NC} Hugging Face - ISSAI"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running.${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

# Create volume if it doesn't exist
echo -e "${GREEN}Ensuring Docker volume exists...${NC}"
docker volume create ${VOLUME_NAME} > /dev/null 2>&1 || true

# Check if model already exists in volume
echo -e "${GREEN}Checking if model already exists...${NC}"
if docker run --rm -v ${VOLUME_NAME}:/models alpine test -f /models/${MODEL_NAME}; then
    echo -e "${GREEN}✓ Model already downloaded!${NC}"
    echo ""
    echo "Model location: Docker volume '${VOLUME_NAME}'"
    echo "File: /models/${MODEL_NAME}"
    exit 0
fi

echo -e "${YELLOW}Model not found. Starting download...${NC}"
echo -e "${YELLOW}This will download ~5GB. Please be patient.${NC}"
echo ""

# Download model using a temporary container with wget
echo -e "${GREEN}Downloading ${MODEL_NAME}...${NC}"
docker run --rm \
    -v ${VOLUME_NAME}:/models \
    alpine sh -c "
        apk add --no-cache wget && \
        cd /models && \
        wget --progress=bar:force:noscroll \
             --show-progress \
             -O ${MODEL_NAME}.tmp \
             '${MODEL_URL}' && \
        mv ${MODEL_NAME}.tmp ${MODEL_NAME}
    "

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ Download complete!"
    echo "==========================================${NC}"
    echo ""
    echo "Model location: Docker volume '${VOLUME_NAME}'"
    echo "File: /models/${MODEL_NAME}"
    echo ""
    echo "The model is now ready to use with llama.cpp service."
else
    echo -e "${RED}✗ Download failed!${NC}"
    echo "Please check your internet connection and try again."
    exit 1
fi
