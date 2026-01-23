#!/bin/bash

# Multi-Model Translation System - GPU Native Startup Script
# This script uses 'docker run --gpus' instead of 'docker compose deploy.resources'
# which works better in WSL2 environments

set -e

echo "=========================================="
echo "Multi-Model Translation System"
echo "GPU Native Mode"
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

echo -e "${GREEN}Step 1: Checking GPU availability...${NC}"
echo ""

# Check if GPU is available
CUDA_AVAILABLE=false
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        CUDA_AVAILABLE=true
        echo -e "${GREEN}✓ NVIDIA GPU detected on host${NC}"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    fi
fi

# Test Docker GPU access
if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    CUDA_AVAILABLE=true
    echo -e "${GREEN}✓ Docker can access GPU${NC}"
else
    echo -e "${RED}✗ Docker cannot access GPU${NC}"
    echo -e "${YELLOW}Falling back to CPU mode...${NC}"
    echo ""
    echo "To enable GPU, ensure NVIDIA Container Toolkit is installed:"
    echo "  sudo apt-get install -y nvidia-container-toolkit"
    echo "  sudo nvidia-ctk runtime configure --runtime=docker"
    echo "  sudo systemctl restart docker"
    echo ""
    echo "Starting in CPU mode instead..."
    exec ./start.sh
fi

echo ""
echo -e "${GREEN}Step 2: Checking KazLLM-8B model configuration...${NC}"
echo ""

GGUF_FILENAME="llama-3.1-kazllm-1.0-8b-q4_k_m.gguf"

# Check if KazLLM model is enabled in config.yaml
KAZLLM_ENABLED=false
if [ -f "config.yaml" ]; then
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
            echo -e "${RED}ERROR: KazLLM-8B GGUF file not found${NC}"
            echo "See DOWNLOAD_KAZLLM.md for instructions"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⊘ KazLLM-8B model is disabled in config.yaml (skipping)${NC}"
fi

echo ""
echo -e "${GREEN}Step 3: Creating Docker network...${NC}"
echo ""

# Create network if it doesn't exist
docker network create translatorbk_translator-network 2>/dev/null || echo -e "${YELLOW}Network already exists${NC}"

# Create volumes
docker volume create translatorbk_ollama_data 2>/dev/null || true

echo ""
echo -e "${GREEN}Step 4: Starting GPU services with native GPU support...${NC}"
echo ""

# Stop and remove old containers if they exist
echo "Cleaning up old containers..."
docker rm -f translator-ollama translator-llamacpp translator-qolda 2>/dev/null || true

# Start Ollama with GPU
echo -e "${YELLOW}Starting Ollama with GPU...${NC}"
docker run -d \
    --name translator-ollama \
    --gpus all \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    -e LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib/wsl/lib \
    -v translatorbk_ollama_data:/root/.ollama \
    -p 11434:11434 \
    --network translatorbk_translator-network \
    --restart unless-stopped \
    ollama/ollama:latest

echo -e "${GREEN}✓ Ollama started with GPU${NC}"

# Check if ISSAI models are enabled
USE_ISSAI_PROFILE=false
if [ -f "config.yaml" ]; then
    if grep -A 3 "name: kazllm-8b" config.yaml | grep -q "enabled: true"; then
        USE_ISSAI_PROFILE=true
    fi
    if grep -A 3 "name: qolda" config.yaml | grep -q "enabled: true"; then
        USE_ISSAI_PROFILE=true
    fi
fi

# Start llamacpp if enabled
if [ "$USE_ISSAI_PROFILE" = true ] && [ "$KAZLLM_ENABLED" = true ]; then
    echo -e "${YELLOW}Starting llama.cpp with GPU...${NC}"
    docker run -d \
        --name translator-llamacpp \
        --gpus all \
        -e NVIDIA_VISIBLE_DEVICES=all \
        -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
        -v translatorbk_kazllm_models:/models \
        -p 8080:8080 \
        --network translatorbk_translator-network \
        --restart unless-stopped \
        ghcr.io/ggml-org/llama.cpp:server-cuda \
        --server --host 0.0.0.0 --port 8080 \
        -m /models/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf \
        -c 4096 -n 512 -ngl 99

    echo -e "${GREEN}✓ llama.cpp started with GPU${NC}"
fi

# Check if qolda is enabled and image exists
if [ "$USE_ISSAI_PROFILE" = true ]; then
    if docker image inspect issai/qolda:latest >/dev/null 2>&1; then
        echo -e "${YELLOW}Starting Qolda with GPU...${NC}"
        docker run -d \
            --name translator-qolda \
            --gpus all \
            -e NVIDIA_VISIBLE_DEVICES=all \
            -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
            -e MODEL_PATH=/app/models \
            -p 8081:8000 \
            --network translatorbk_translator-network \
            --restart unless-stopped \
            issai/qolda:latest

        echo -e "${GREEN}✓ Qolda started with GPU${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Step 5: Starting backend and frontend with docker compose...${NC}"
echo ""

# Start backend and frontend without dependencies check
# (ollama is already running from docker run above)
docker compose up -d --no-deps backend frontend

echo ""
echo -e "${GREEN}Step 6: Waiting for services to be ready...${NC}"
echo ""

# Wait for Ollama to be ready
echo "Waiting for Ollama..."
MAX_WAIT=60
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if docker exec translator-ollama ollama list &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is ready!${NC}"
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

# Check and pull required models
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

echo ""
echo -e "${GREEN}Step 7: Verifying GPU usage...${NC}"
echo ""

# Check GPU detection in Ollama
sleep 3
GPU_DETECTED=$(docker logs translator-ollama 2>&1 | grep -i "vram" | tail -1)
if echo "$GPU_DETECTED" | grep -q '"0 B"'; then
    echo -e "${RED}⚠ WARNING: Ollama still shows 0 B VRAM${NC}"
    echo "This shouldn't happen with docker run --gpus all"
    echo "Check logs: docker logs translator-ollama"
else
    echo -e "${GREEN}✓ GPU appears to be detected by Ollama${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "System is ready!"
echo "==========================================${NC}"
echo ""
echo "Access the application:"
echo -e "  ${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "  ${GREEN}Backend API:${NC} http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC} http://localhost:8000/api/docs"
echo ""
echo "GPU Services:"
echo -e "  ${GREEN}Ollama:${NC} http://localhost:11434"
if [ "$KAZLLM_ENABLED" = true ]; then
    echo -e "  ${GREEN}llama.cpp:${NC} http://localhost:8080"
fi
echo ""
echo "To view logs:"
echo "  docker logs -f translator-ollama"
echo "  docker compose logs -f backend"
echo ""
echo "To verify GPU usage:"
echo "  docker logs translator-ollama | grep -i vram"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "To stop the system:"
echo "  docker stop translator-ollama translator-llamacpp translator-qolda 2>/dev/null || true"
echo "  docker compose down"
echo ""
