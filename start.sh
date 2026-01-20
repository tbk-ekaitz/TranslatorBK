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

echo -e "${GREEN}Starting services...${NC}"
echo ""

# Start Docker Compose
docker compose up -d

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

# Check and pull required models
MODELS=("llama3" "qwen2")

for MODEL in "${MODELS[@]}"; do
    if docker exec translator-ollama ollama list | grep -q "$MODEL"; then
        echo -e "${GREEN}✓ Model '$MODEL' is already installed${NC}"
    else
        echo -e "${YELLOW}Downloading model '$MODEL'... This may take a while.${NC}"
        docker exec translator-ollama ollama pull "$MODEL"
        echo -e "${GREEN}✓ Model '$MODEL' installed successfully${NC}"
    fi
done

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
