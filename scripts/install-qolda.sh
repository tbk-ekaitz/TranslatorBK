#!/bin/bash
# scripts/install-qolda.sh

echo "⚠️  Qolda Docker image not found locally."
echo "🔄 Cloning and building official ISSAI/Qolda-deployment..."

# Crear temporal, clonar, build y limpiar
TEMP_DIR=$(mktemp -d)
git clone https://github.com/IS2AI/Qolda-deployment.git "$TEMP_DIR"
docker build -t issai/qolda:latest "$TEMP_DIR"
rm -rf "$TEMP_DIR"

echo "✅ Qolda image built successfully!"