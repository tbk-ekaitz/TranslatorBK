#!/bin/bash

# Script to test GPU access from Docker containers

echo "=========================================="
echo "GPU Access Test"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Test 1: Host GPU detection${NC}"
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ nvidia-smi works on host${NC}"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        echo -e "${RED}✗ nvidia-smi failed on host${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ nvidia-smi not found on host${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Test 2: Docker GPU access test${NC}"
if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ Docker can access GPU${NC}"
    docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${RED}✗ Docker cannot access GPU${NC}"
    echo ""
    echo -e "${YELLOW}This means NVIDIA Container Toolkit is not properly configured.${NC}"
    echo ""
    echo "To fix this, install NVIDIA Container Toolkit:"
    echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    echo ""
    echo "For WSL2, you may need:"
    echo "  1. Install NVIDIA drivers in Windows"
    echo "  2. Update WSL2 kernel"
    echo "  3. Install nvidia-container-toolkit in WSL2"
    exit 1
fi

echo ""
echo -e "${YELLOW}Test 3: Check if Ollama container can see GPU${NC}"
if docker ps --format '{{.Names}}' | grep -q "translator-ollama"; then
    echo "Checking Ollama container..."
    # Check if nvidia-smi works inside the container
    if docker exec translator-ollama nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ Ollama container can access GPU${NC}"
        docker exec translator-ollama nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        echo -e "${RED}✗ Ollama container cannot access GPU${NC}"
        echo "Container needs to be restarted with proper GPU configuration"
    fi
else
    echo -e "${YELLOW}⊘ Ollama container not running${NC}"
fi

echo ""
echo "=========================================="
echo "Test complete!"
echo "=========================================="
