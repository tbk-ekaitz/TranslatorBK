# Multi-Model Translation System

A sophisticated web-based translation application that leverages multiple AI models to provide high-quality translations from English or Traditional Chinese to Russian and Kazakh simultaneously.

## Features

- **Multi-Model Translation**: Uses multiple AI models (local via Ollama + external APIs) to generate translations
- **Intelligent Selection**: Automatically evaluates and selects the best translation from multiple candidates
- **Dual Source Languages**: Supports English and Traditional Chinese as source languages (mutually exclusive inputs)
- **Dual Target Languages**: Translates to Russian and Kazakh simultaneously
- **Modern Web UI**: Clean, responsive React-based interface with real-time feedback
- **Containerized**: Fully containerized with Docker for easy deployment
- **Configurable**: Easy configuration via YAML for models and translation settings
- **Multiple Evaluation Methods**: Choose between consensus, scoring, or weighted voting for translation selection

## Architecture

The system consists of three main components:

1. **Frontend**: React + Vite application with a modern, responsive UI
2. **Backend**: FastAPI-based REST API that orchestrates translation across multiple models
3. **Ollama**: Local AI model server for running open-source LLMs

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend   │─────▶│   Ollama    │
│  (React)    │◀─────│  (FastAPI)  │◀─────│  (LLMs)     │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ├──────▶ OpenAI API (optional)
                            ├──────▶ Anthropic API (optional)
                            └──────▶ Google AI API (optional)
```

## Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- At least 8GB RAM (16GB recommended for multiple models)
- 20GB+ free disk space (for AI models)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TranslatorBK
```

### 2. Configure Environment (Optional)

If you plan to use external API models (OpenAI, Anthropic, Google), copy the example environment file and add your API keys:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

The system works out-of-the-box with local Ollama models without any API keys.

### 3. Start the System

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

The startup script will:
- Check Docker installation
- Create `.env` file if it doesn't exist
- Start all services
- Download required Ollama models (llama3, qwen2)
- Display access URLs when ready

### 4. Access the Application

Once started, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. **Select Source Language**: Click on either the English or Traditional Chinese input field
2. **Enter Text**: Type or paste the text you want to translate
3. **Translate**: Click the "Translate" button
4. **View Results**: See translations in Russian and Kazakh with confidence scores

### Input Behavior

- The input fields are **mutually exclusive**
- Clicking on one input automatically:
  - Deactivates the other input
  - Clears any text in the inactive input
  - Makes it uneditable
- You can switch between languages by clicking on the other input field

## Configuration

### Model Configuration (`config.yaml`)

Configure which AI models to use for translation:

```yaml
models:
  # Local Ollama models
  - name: llama3
    type: ollama
    model_id: llama3
    weight: 1.0
    enabled: true
    timeout: 60

  # External API models (configure API keys in .env)
  - name: gpt-4
    type: openai
    model_id: gpt-4-turbo-preview
    weight: 1.5
    enabled: false  # Set to true to enable
    timeout: 60
```

**Supported Model Types:**
- `ollama`: Local models via Ollama
- `openai`: OpenAI GPT models
- `anthropic`: Anthropic Claude models
- `google`: Google Gemini models

### Environment Variables (`.env`)

```bash
# API Keys (only needed for external models)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434

# Evaluation Settings
EVALUATION_METHOD=consensus  # consensus, scoring, weighted_vote
CONSENSUS_THRESHOLD=0.7
```

### Translation Prompts

Customize translation prompts per target language in `config.yaml`:

```yaml
translation:
  ru:  # Russian
    system_prompt: "You are a professional translator..."
    temperature: 0.3
    max_tokens: 2000
  kk:  # Kazakh
    system_prompt: "You are a professional translator..."
    temperature: 0.3
    max_tokens: 2000
```

## Evaluation Methods

The system supports three methods for selecting the best translation:

1. **Consensus** (default): Groups similar translations and selects the most common one
2. **Scoring**: Evaluates translations based on length consistency, character variety, and similarity
3. **Weighted Vote**: Uses model weights to influence selection

Configure in `.env`:
```bash
EVALUATION_METHOD=consensus
```

## Docker Commands

### View Logs
```bash
docker compose logs -f
```

### View Specific Service Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f ollama
```

### Stop the System
```bash
docker compose down
```

### Stop and Remove All Data
```bash
docker compose down -v
```

### Restart Services
```bash
docker compose restart
```

### Rebuild After Code Changes
```bash
docker compose up -d --build
```

## Adding New Models

### Local Ollama Models

1. Install a model in Ollama:
```bash
docker exec translator-ollama ollama pull <model-name>
```

2. Add to `config.yaml`:
```yaml
models:
  - name: my-model
    type: ollama
    model_id: <model-name>
    weight: 1.0
    enabled: true
```

### External API Models

1. Add API key to `.env`:
```bash
OPENAI_API_KEY=your_key_here
```

2. Enable the model in `config.yaml`:
```yaml
models:
  - name: gpt-4
    type: openai
    model_id: gpt-4-turbo-preview
    weight: 1.5
    enabled: true  # Change to true
```

3. Restart the backend:
```bash
docker compose restart backend
```

## Project Structure

```
TranslatorBK/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main FastAPI application
│   │   ├── config.py       # Configuration management
│   │   ├── models.py       # Pydantic models
│   │   └── services/
│   │       ├── translator.py  # Translation service
│   │       └── evaluator.py   # Evaluation service
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       └── TranslationPanel.jsx
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── config.yaml            # Model and translation configuration
├── .env.example          # Example environment variables
├── docker compose.yml    # Docker Compose configuration
├── start.sh             # Linux/Mac startup script
├── start.bat            # Windows startup script
└── README.md            # This file
```

## API Endpoints

### POST `/translate`

Translate text from source language to Russian and Kazakh.

**Request:**
```json
{
  "text": "Hello world",
  "source_language": "en"
}
```

**Response:**
```json
{
  "russian": {
    "target_language": "ru",
    "best_translation": "Привет, мир",
    "all_translations": [...],
    "evaluation_method": "consensus",
    "evaluation_score": 0.95
  },
  "kazakh": {
    "target_language": "kk",
    "best_translation": "Сәлем Әлем",
    "all_translations": [...],
    "evaluation_method": "consensus",
    "evaluation_score": 0.92
  },
  "source_language": "en",
  "source_text": "Hello world",
  "total_processing_time": 2.5
}
```

### GET `/health`

Check API health and available models.

### GET `/models`

Get list of configured models and their status.

For full API documentation, visit http://localhost:8000/docs when the system is running.

## Troubleshooting

### Ollama Models Not Downloading

If models fail to download automatically:

```bash
docker exec -it translator-ollama bash
ollama pull llama3
ollama pull qwen2
exit
```

### Port Already in Use

If ports 3000, 8000, or 11434 are already in use, edit `docker compose.yml` to use different ports:

```yaml
services:
  frontend:
    ports:
      - "3001:80"  # Change 3000 to 3001
```

### Services Not Starting

Check logs for errors:
```bash
docker compose logs -f
```

Ensure Docker has enough resources allocated (8GB+ RAM recommended).

### Translation Fails

1. Check that Ollama models are downloaded: `docker exec translator-ollama ollama list`
2. Verify backend can reach Ollama: `docker compose logs backend`
3. Check API keys if using external models

## Performance Optimization

- **Reduce Model Count**: Fewer models = faster translations
- **Use Model Weights**: Assign higher weights to better models
- **Adjust Timeouts**: Increase timeouts in `config.yaml` for slow models
- **Cache Translations**: Enable caching in `.env` (enabled by default)

## Security Considerations

- Never commit `.env` file with real API keys
- Use environment-specific `.env` files for different deployments
- Consider using Docker secrets for production deployments
- Review and restrict CORS origins in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with `docker compose up --build`
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue in the repository
- Check existing issues for solutions
- Review Docker logs for error messages

## Acknowledgments

- Ollama for local LLM inference
- FastAPI for the backend framework
- React and Vite for the frontend
- OpenAI, Anthropic, and Google for their AI APIs
