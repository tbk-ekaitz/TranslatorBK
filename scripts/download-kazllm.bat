@echo off
REM Script to download KazLLM-8B GGUF model for llama.cpp
REM This script downloads the model into the Docker volume

echo ==========================================
echo KazLLM-8B Model Downloader
echo ==========================================
echo.

REM Model information
set MODEL_NAME=llama-3.1-kazllm-1.0-8b-q4_k_m.gguf
set MODEL_URL=https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B-GGUF4/resolve/main/%MODEL_NAME%
set VOLUME_NAME=translatorbk_kazllm_models

echo Model: %MODEL_NAME%
echo Size: ~5GB (Q4_K_M quantization)
echo Source: Hugging Face - ISSAI
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Create volume if it doesn't exist
echo Ensuring Docker volume exists...
docker volume create %VOLUME_NAME% >nul 2>&1

REM Check if model already exists in volume
echo Checking if model already exists...
docker run --rm -v %VOLUME_NAME%:/models alpine test -f /models/%MODEL_NAME% >nul 2>&1
if not errorlevel 1 (
    echo Model already downloaded!
    echo.
    echo Model location: Docker volume '%VOLUME_NAME%'
    echo File: /models/%MODEL_NAME%
    pause
    exit /b 0
)

echo Model not found. Starting download...
echo This will download ~5GB. Please be patient.
echo.

REM Download model using a temporary container with wget
echo Downloading %MODEL_NAME%...
docker run --rm -v %VOLUME_NAME%:/models alpine sh -c "apk add --no-cache wget && cd /models && wget --progress=bar:force:noscroll --show-progress -O %MODEL_NAME%.tmp '%MODEL_URL%' && mv %MODEL_NAME%.tmp %MODEL_NAME%"

if errorlevel 1 (
    echo.
    echo Download failed!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Download complete!
echo ==========================================
echo.
echo Model location: Docker volume '%VOLUME_NAME%'
echo File: /models/%MODEL_NAME%
echo.
echo The model is now ready to use with llama.cpp service.
echo.
pause
