#!/bin/bash

# Multi-Model Translation System - Startup Script (Linux/Mac)
# This script starts the entire translation system using Docker Compose

set -e

echo "=========================================="
echo "Multi-Model Translation System"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists, if not, copy from example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please edit it with your API keys if using external models.${NC}"
    else
        echo -e "${RED}Error: .env.example not found.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Step 1: Checking KazLLM-8B model configuration...${NC}"
echo ""

GGUF_FILENAME="llama-3.1-kazllm-1.0-8b-q4_k_m.gguf"

# Check if KazLLM model is enabled in config.yaml
KAZLLM_ENABLED=false
if [ -f "config.yaml" ]; then
    # Simple grep to check if kazllm-8b is enabled
    if grep -A 3 "name: kazllm-8b" config.yaml | grep -q "enabled: true"; then
        KAZLLM_ENABLED=true
    fi
fi

# Only proceed if model is enabled
if [ "$KAZLLM_ENABLED" = true ]; then
    # Create Docker volume
    docker volume create translatorbk_kazllm_models > /dev/null 2>&1 || true

    # Check if GGUF exists in Docker volume
    KAZLLM_IN_VOLUME=false
    if docker run --rm -v translatorbk_kazllm_models:/models alpine test -f /models/${GGUF_FILENAME} 2>/dev/null; then
        KAZLLM_IN_VOLUME=true
    fi

    if [ "$KAZLLM_IN_VOLUME" = true ]; then
        echo -e "${GREEN}✓ KazLLM-8B GGUF file found in Docker volume${NC}"
    else
        # Check if GGUF file exists in current directory
        if [ -f "${GGUF_FILENAME}" ]; then
            echo -e "${YELLOW}Found ${GGUF_FILENAME} in current directory${NC}"
            echo -e "${YELLOW}Copying to Docker volume...${NC}"

            docker run --rm \
                -v "$(pwd):/source" \
                -v translatorbk_kazllm_models:/models \
                alpine cp /source/${GGUF_FILENAME} /models/

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ GGUF file successfully copied to Docker volume${NC}"
            else
                echo -e "${RED}✗ Failed to copy GGUF file to Docker volume${NC}"
                exit 1
            fi
        else
            # GGUF not found anywhere
            echo -e "${RED}=========================================="
            echo "ERROR: KazLLM-8B GGUF file not found"
            echo "==========================================${NC}"
            echo ""
            echo -e "${YELLOW}The KazLLM-8B model is enabled but the GGUF file is missing.${NC}"
            echo ""
            echo "You have two options:"
            echo ""
            echo -e "${GREEN}Option 1: Add the GGUF file${NC}"
            echo "  Place the file '${GGUF_FILENAME}' in this directory:"
            echo "  $(pwd)/${GGUF_FILENAME}"
            echo ""
            echo "  Then run this script again. The file will be automatically copied to Docker."
            echo ""
            echo -e "${GREEN}Option 2: Disable the model${NC}"
            echo "  Edit config.yaml and set 'enabled: false' for kazllm-8b model"
            echo ""
            echo "For download instructions, see: DOWNLOAD_KAZLLM.md"
            echo ""
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⊘ KazLLM-8B model is disabled in config.yaml (skipping)${NC}"
fi

echo ""
echo -e "${GREEN}Step 2: Detecting CUDA availability...${NC}"
echo ""

# Detect if CUDA/GPU is available
CUDA_AVAILABLE=false

# Try to detect NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        CUDA_AVAILABLE=true
        echo -e "${GREEN}✓ NVIDIA GPU detected (CUDA available via nvidia-smi)${NC}"
    fi
fi

# If nvidia-smi not found, try Docker GPU test
if [ "$CUDA_AVAILABLE" = false ]; then
    if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
        CUDA_AVAILABLE=true
        echo -e "${GREEN}✓ NVIDIA GPU detected (CUDA available via Docker)${NC}"
    else
        echo -e "${YELLOW}⚠ No NVIDIA GPU detected - services will start but GPU acceleration may not work${NC}"
        echo -e "${YELLOW}  Check: 1) NVIDIA drivers installed, 2) nvidia-container-toolkit installed${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Step 3: Starting Docker services...${NC}"
echo ""

# Check if any ISSAI models are enabled (kazllm-8b or qolda)
USE_ISSAI_PROFILE=false
if [ -f "config.yaml" ]; then
    if grep -A 3 "name: kazllm-8b" config.yaml | grep -q "enabled: true"; then
        USE_ISSAI_PROFILE=true
    fi
    if grep -A 3 "name: qolda" config.yaml | grep -q "enabled: true"; then
        USE_ISSAI_PROFILE=true
        # Si Qolda está activado pero no tenemos la imagen, la construimos ahora mismo.
        if ! docker image inspect issai/qolda:latest >/dev/null 2>&1; then
            echo "Qolda is enabled but image is missing. Building automatically..."
            # Aseguramos permisos por si acaso y ejecutamos
            chmod +x ./scripts/install-qolda.sh
            ./scripts/install-qolda.sh
        fi
    fi
fi

# Start Docker Compose with or without ISSAI profile
if [ "$USE_ISSAI_PROFILE" = true ]; then
    echo -e "${YELLOW}Starting with ISSAI models (llamacpp/qolda)...${NC}"
    docker compose --profile issai up -d
else
    echo -e "${YELLOW}Starting core services only (Ollama models)...${NC}"
    docker compose up -d
fi

echo ""
echo -e "${GREEN}Services are starting up...${NC}"
echo ""
echo "Waiting for Ollama to be ready..."

# Wait for Ollama to be ready
MAX_WAIT=60
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if docker exec translator-ollama ollama list &> /dev/null; then
        echo -e "${GREEN}Ollama is ready!${NC}"
        break
    fi
    sleep 2
    COUNTER=$((COUNTER + 2))
    echo -n "."
done

if [ $COUNTER -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}Warning: Ollama may not be fully ready yet.${NC}"
fi

echo ""
echo "Checking if required models are installed..."
echo ""

# Check and pull required models for Kazakh/Russian translation
# These models are confirmed to work with Ollama
declare -A MODELS=(
    ["llama3.1"]="llama3.1"
    ["qwen2.5"]="qwen2.5"
    ["t-pro-it-2.0"]="t-tech/t-pro-it-2.0:q4_k_m"
)

echo -e "${GREEN}Downloading Ollama models for translation...${NC}"
echo ""

for MODEL_NAME in "${!MODELS[@]}"; do
    PULL_CMD="${MODELS[$MODEL_NAME]}"

    if docker exec translator-ollama ollama list | grep -q "$MODEL_NAME"; then
        echo -e "${GREEN}✓ Model '$MODEL_NAME' is already installed${NC}"
    else
        echo -e "${YELLOW}Downloading model '$MODEL_NAME' ($PULL_CMD)...${NC}"
        echo -e "${YELLOW}This may take a while depending on model size and your internet speed.${NC}"

        docker exec translator-ollama ollama pull "$PULL_CMD"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Model '$MODEL_NAME' installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install model '$MODEL_NAME'${NC}"
            echo -e "${YELLOW}  Continuing anyway - other models may still work${NC}"
        fi
    fi
    echo ""
done

echo -e "${GREEN}Model installation complete!${NC}"
echo ""
echo -e "${YELLOW}Note: T-pro-it-2.0 requires significant resources (20GB+ VRAM).${NC}"
echo -e "${YELLOW}If it failed, you can still use llama3.1 and qwen2.5 for translations.${NC}"
echo ""

echo ""
echo -e "${GREEN}=========================================="
echo "System is ready!"
echo "==========================================${NC}"
echo ""
echo "Access the application:"
echo -e "  ${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "  ${GREEN}Backend API:${NC} http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop the system:"
echo "  docker compose down"
echo ""
echo "To stop and remove all data:"
echo "  docker compose down -v"
echo ""
