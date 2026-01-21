@echo off
REM Multi-Model Translation System - Startup Script (Windows)
REM This script starts the entire translation system using Docker Compose

echo ==========================================
echo Multi-Model Translation System
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed.
    echo Please install Docker Desktop from https://www.docker.com/get-started
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo Error: Docker Compose is not installed.
        echo Please install Docker Compose from https://docs.docker.com/compose/install/
        pause
        exit /b 1
    )
)

REM Check if .env file exists, if not, copy from example
if not exist .env (
    echo Warning: .env file not found. Creating from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo .env file created. Please edit it with your API keys if using external models.
    ) else (
        echo Error: .env.example not found.
        pause
        exit /b 1
    )
)

echo Step 1: Checking KazLLM-8B model configuration...
echo.

set GGUF_FILENAME=llama-3.1-kazllm-1.0-8b-q4_k_m.gguf

REM Check if KazLLM model is enabled in config.yaml
set KAZLLM_ENABLED=false
if exist "config.yaml" (
    findstr /C:"name: kazllm-8b" config.yaml >nul 2>&1
    if not errorlevel 1 (
        findstr /C:"enabled: true" config.yaml >nul 2>&1
        if not errorlevel 1 (
            set KAZLLM_ENABLED=true
        )
    )
)

REM Only proceed if model is enabled
if "%KAZLLM_ENABLED%"=="true" (
    REM Create Docker volume
    docker volume create translatorbk_kazllm_models >nul 2>&1

    REM Check if GGUF exists in Docker volume
    docker run --rm -v translatorbk_kazllm_models:/models alpine test -f /models/%GGUF_FILENAME% >nul 2>&1
    set KAZLLM_IN_VOLUME=%errorlevel%

    if "%KAZLLM_IN_VOLUME%"=="0" (
        echo [32m✓ KazLLM-8B GGUF file found in Docker volume[0m
    ) else (
        REM Check if GGUF file exists in current directory
        if exist "%GGUF_FILENAME%" (
            echo [33mFound %GGUF_FILENAME% in current directory[0m
            echo [33mCopying to Docker volume...[0m

            docker run --rm -v "%cd%:/source" -v translatorbk_kazllm_models:/models alpine cp /source/%GGUF_FILENAME% /models/

            if not errorlevel 1 (
                echo [32m✓ GGUF file successfully copied to Docker volume[0m
            ) else (
                echo [31m✗ Failed to copy GGUF file to Docker volume[0m
                pause
                exit /b 1
            )
        ) else (
            REM GGUF not found anywhere
            echo ==========================================
            echo ERROR: KazLLM-8B GGUF file not found
            echo ==========================================
            echo.
            echo The KazLLM-8B model is enabled but the GGUF file is missing.
            echo.
            echo You have two options:
            echo.
            echo Option 1: Add the GGUF file
            echo   Place the file '%GGUF_FILENAME%' in this directory:
            echo   %cd%\%GGUF_FILENAME%
            echo.
            echo   Then run this script again. The file will be automatically copied to Docker.
            echo.
            echo Option 2: Disable the model
            echo   Edit config.yaml and set 'enabled: false' for kazllm-8b model
            echo.
            echo For download instructions, see: DOWNLOAD_KAZLLM.md
            echo.
            pause
            exit /b 1
        )
    )
) else (
    echo [33m⊘ KazLLM-8B model is disabled in config.yaml (skipping)[0m
)

echo.
echo Step 2: Starting Docker services...
echo.

REM Start Docker Compose
docker compose up -d

echo.
echo Services are starting up...
echo.
echo Waiting for Ollama to be ready...

REM Wait for Ollama to be ready
set MAX_WAIT=60
set COUNTER=0

:wait_ollama
docker exec translator-ollama ollama list >nul 2>&1
if errorlevel 1 (
    if %COUNTER% LSS %MAX_WAIT% (
        timeout /t 2 /nobreak >nul
        set /a COUNTER+=2
        echo|set /p="."
        goto wait_ollama
    ) else (
        echo.
        echo Warning: Ollama may not be fully ready yet.
    )
) else (
    echo.
    echo Ollama is ready!
)

echo.
echo Checking if required models are installed...
echo.

REM Check and pull required models for Kazakh/Russian translation
echo Downloading Ollama models for translation...
echo.

call :check_model llama3.1 llama3.1
call :check_model qwen2.5 qwen2.5
call :check_model t-pro-it-2.0 t-tech/t-pro-it-2.0:q4_k_m

echo.
echo Model installation complete!
echo.
echo Note: T-pro-it-2.0 requires significant resources (20GB+ VRAM).
echo If it failed, you can still use llama3.1 and qwen2.5 for translations.
echo.

goto :after_models

:check_model
set model_name=%1
set pull_cmd=%2
docker exec translator-ollama ollama list | find "%model_name%" >nul 2>&1
if errorlevel 1 (
    echo Downloading model '%model_name%' ^(%pull_cmd%^)...
    echo This may take a while depending on model size and your internet speed.
    docker exec translator-ollama ollama pull %pull_cmd%
    if errorlevel 1 (
        echo Failed to install model '%model_name%'
        echo Continuing anyway - other models may still work
    ) else (
        echo Model '%model_name%' installed successfully
    )
) else (
    echo Model '%model_name%' is already installed
)
echo.
goto :eof

:after_models

echo.
echo ==========================================
echo System is ready!
echo ==========================================
echo.
echo Access the application:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo To view logs:
echo   docker compose logs -f
echo.
echo To stop the system:
echo   docker compose down
echo.
echo To stop and remove all data:
echo   docker compose down -v
echo.
pause
