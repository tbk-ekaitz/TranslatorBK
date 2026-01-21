#!/bin/bash

# Script to verify that all services and models are properly set up

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "Multi-Model Translation System"
echo "Setup Verification"
echo "==========================================${NC}"
echo ""

# Check Docker is running
echo -n "Checking Docker... "
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi

# Check containers are running
echo ""
echo "Checking containers:"

containers=("translator-ollama" "translator-llamacpp" "translator-qolda" "translator-backend" "translator-frontend")
all_healthy=true

for container in "${containers[@]}"; do
    echo -n "  $container... "
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
            echo -e "${GREEN}✓ Running${NC}"
        else
            echo -e "${YELLOW}⚠ Running but not healthy (status: $health)${NC}"
            all_healthy=false
        fi
    else
        echo -e "${RED}✗ Not running${NC}"
        all_healthy=false
    fi
done

# Check KazLLM model
echo ""
echo -n "Checking KazLLM-8B model... "
if docker run --rm -v translatorbk_kazllm_models:/models alpine test -f /models/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf 2>/dev/null; then
    echo -e "${GREEN}✓ Downloaded${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo -e "${YELLOW}  To download:${NC}"
    echo -e "${YELLOW}    1. Get HF token: https://huggingface.co/settings/tokens${NC}"
    echo -e "${YELLOW}    2. Run: ./scripts/download-kazllm.sh YOUR_TOKEN${NC}"
    echo -e "${YELLOW}  Or without token (may fail): ./scripts/download-kazllm.sh${NC}"
    all_healthy=false
fi

# Check Ollama models
echo ""
echo "Checking Ollama models:"
for model in "llama3.1" "qwen2.5" "t-pro-it"; do
    echo -n "  $model... "
    if docker exec translator-ollama ollama list 2>/dev/null | grep -q "$model"; then
        echo -e "${GREEN}✓ Installed${NC}"
    else
        echo -e "${YELLOW}⚠ Not installed${NC}"
    fi
done

# Test API endpoint
echo ""
echo -n "Checking backend API... "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
    all_healthy=false
fi

# Test frontend
echo -n "Checking frontend... "
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
    all_healthy=false
fi

# Summary
echo ""
echo "=========================================="
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo "You can now use the translation system:"
    echo "  Frontend: http://localhost:3000"
    echo "  API Docs: http://localhost:8000/docs"
else
    echo -e "${YELLOW}⚠ Some components need attention${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - View logs: docker compose logs -f"
    echo "  - Restart: docker compose restart"
    echo "  - Full restart: docker compose down && docker compose up -d"
fi
echo "=========================================="
