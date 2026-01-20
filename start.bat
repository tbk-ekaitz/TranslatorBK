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

echo Starting services...
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

REM Check and pull required models
for %%M in (llama3 qwen2) do (
    docker exec translator-ollama ollama list | find "%%M" >nul 2>&1
    if errorlevel 1 (
        echo Downloading model '%%M'... This may take a while.
        docker exec translator-ollama ollama pull %%M
        echo Model '%%M' installed successfully
    ) else (
        echo Model '%%M' is already installed
    )
)

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
