#!/bin/bash

# Script to diagnose GPU detection issues in Ollama

echo "=========================================="
echo "GPU Diagnosis for Ollama"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "translator-ollama"; then
    echo -e "${RED}✗ Ollama container is not running${NC}"
    echo "Start it with: docker compose up -d"
    exit 1
fi

echo -e "${GREEN}Ollama container is running${NC}"
echo ""

echo "1. Checking nvidia-smi in container:"
echo "-----------------------------------"
docker exec translator-ollama nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1 || echo "nvidia-smi failed"
echo ""

echo "2. Checking CUDA environment variables:"
echo "---------------------------------------"
docker exec translator-ollama env | grep -E "CUDA|NVIDIA|LD_LIBRARY" | sort
echo ""

echo "3. Checking for CUDA libraries:"
echo "-------------------------------"
docker exec translator-ollama sh -c "find /usr -name 'libcuda.so*' 2>/dev/null" || echo "No CUDA libraries found in /usr"
echo ""

echo "4. Checking LD_LIBRARY_PATH locations:"
echo "--------------------------------------"
docker exec translator-ollama sh -c "ls -la /usr/local/nvidia/lib* 2>/dev/null" || echo "/usr/local/nvidia/lib not found"
echo ""

echo "5. Checking Ollama GPU detection:"
echo "---------------------------------"
docker exec translator-ollama ollama ps 2>&1 || echo "No models running"
echo ""

echo "6. Recent Ollama logs about GPU:"
echo "--------------------------------"
docker logs translator-ollama 2>&1 | grep -i -E "gpu|cuda|vram|nvidia|offload" | tail -20
echo ""

echo "=========================================="
echo "Diagnosis complete!"
echo "=========================================="
echo ""
echo "If you see 'total vram: 0 B', the issue is that Ollama cannot find CUDA libraries."
echo "This typically means:"
echo "  1. NVIDIA Container Toolkit is not properly configured"
echo "  2. CUDA libraries are not mounted in the expected location"
echo "  3. Docker daemon needs to be configured for GPU support"
echo ""
echo "To fix:"
echo "  1. Ensure NVIDIA Container Toolkit is installed:"
echo "     sudo apt-get install -y nvidia-container-toolkit"
echo "  2. Configure Docker daemon:"
echo "     sudo nvidia-ctk runtime configure --runtime=docker"
echo "     sudo systemctl restart docker"
echo "  3. Restart containers:"
echo "     docker compose down && docker compose up -d"
