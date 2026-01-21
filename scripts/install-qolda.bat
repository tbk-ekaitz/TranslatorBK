@echo off
echo ⚠️  Qolda Docker image not found locally.
echo 🔄 Cloning and building official ISSAI/Qolda-deployment...

REM Crear directorio temporal seguro
set "TEMP_DIR=%TEMP%\qolda_build_%RANDOM%"
mkdir "%TEMP_DIR%"

REM Clonar el repo
git clone https://github.com/IS2AI/Qolda-deployment.git "%TEMP_DIR%"

REM Construir la imagen
echo 🔨 Building Docker image...
docker build -t issai/qolda:latest "%TEMP_DIR%"

REM Limpiar
rmdir /s /q "%TEMP_DIR%"

echo ✅ Qolda image built successfully!