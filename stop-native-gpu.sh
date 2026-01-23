#!/bin/bash

# Stop script for GPU Native Mode

echo "Stopping Translation System (GPU Native Mode)..."
echo ""

# Stop GPU containers
echo "Stopping GPU services..."
docker stop translator-ollama 2>/dev/null && echo "✓ Ollama stopped" || echo "⊘ Ollama not running"
docker stop translator-llamacpp 2>/dev/null && echo "✓ llama.cpp stopped" || echo "⊘ llama.cpp not running"
docker stop translator-qolda 2>/dev/null && echo "✓ Qolda stopped" || echo "⊘ Qolda not running"

# Remove GPU containers
echo ""
echo "Removing GPU containers..."
docker rm translator-ollama 2>/dev/null && echo "✓ Ollama removed" || true
docker rm translator-llamacpp 2>/dev/null && echo "✓ llama.cpp removed" || true
docker rm translator-qolda 2>/dev/null && echo "✓ Qolda removed" || true

# Stop docker compose services
echo ""
echo "Stopping backend and frontend..."
docker compose down

echo ""
echo "✓ All services stopped"
echo ""
echo "To remove all data (volumes), run:"
echo "  docker volume rm translatorbk_ollama_data translatorbk_kazllm_models"
