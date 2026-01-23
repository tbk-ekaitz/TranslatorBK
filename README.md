# Multi-Model Translation System

A sophisticated web-based translation application that leverages multiple AI models to provide high-quality translations from English or Traditional Chinese to Russian and Kazakh simultaneously.

## Features

- **Multi-Model Translation**: Uses multiple AI models (local via Ollama + external APIs) to generate translations
- **Intelligent Selection**: Automatically evaluates and selects the best translation from multiple candidates
- **Dual Source Languages**: Supports English and Traditional Chinese as source languages (mutually exclusive inputs)
- **Dual Target Languages**: Translates to Russian and Kazakh simultaneously
- **Document Translation**: Upload and translate entire documents (PDF, DOCX, TXT, MD) with automatic text extraction and reconstruction
- **Real-time Progress**: Track document translation progress with live updates and progress bars
- **Multiple Export Formats**: Download translated documents as Markdown or JSON with all phrase translations
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

### 2. (Optional) Add ISSAI Specialized Models

The system works out-of-the-box with **Ollama models** (llama3.1, qwen2.5, t-pro-it-2.0). ISSAI models are **optional** and **disabled by default**.

#### KazLLM-8B (Optional - Best for Kazakh)

If you have the `llama-3.1-kazllm-1.0-8b-q4_k_m.gguf` file (~5GB):

1. Place it in the `TranslatorBK/` directory
2. Edit `config.yaml` and set `kazllm-8b` → `enabled: true`
3. Run `./start.sh` or `start.bat`

The startup script will automatically copy it to Docker.

> For download instructions with Hugging Face authentication, see [DOWNLOAD_KAZLLM.md](DOWNLOAD_KAZLLM.md)

#### Qolda (Optional - Requires Custom Deployment)

Qolda Docker image is not publicly available. See [ISSAI_MODELS.md](ISSAI_MODELS.md) for advanced setup.

### 3. Configure Environment (Optional)

If you plan to use external API models (OpenAI, Anthropic, Google), copy the example environment file and add your API keys:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

The system works out-of-the-box with local Ollama models without any API keys.

### 4. Start the System

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

### 5. Access the Application

Once started, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

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

## Document Translation

The system supports translating entire documents while preserving their structure.

### Accessing Document Translation

Navigate to the **Document Translation** page:
- Click "Document Translation" in the navigation menu, or
- Visit http://localhost:3000/document directly

### Supported Formats

- **PDF** (.pdf) - Portable Document Format
- **DOCX** (.docx) - Microsoft Word documents
- **TXT** (.txt) - Plain text files
- **MD** (.md) - Markdown files

### How to Use

1. **Upload a Document**
   - Click "Choose File" and select your document (PDF, DOCX, TXT, or MD)
   - Select the source language (English or Traditional Chinese)
   - Click "Translate Document"
   - You'll receive a unique **Job ID** for tracking

2. **Track Translation Progress**
   - After upload, the Job ID is **automatically filled** in the status section
   - Progress updates **every 500ms** in real-time
   - You'll see:
     - Current status (Pending/Processing/Completed/Failed)
     - Progress bar showing percentage complete
     - Number of phrases translated vs. total phrases

3. **Download Translated Documents**
   - Once completed, four download options appear:
     - **Russian Translation** - Document translated to Russian (Markdown)
     - **Kazakh Translation** - Document translated to Kazakh (Markdown)
     - **Original (MD)** - Original document converted to Markdown
     - **JSON Export** - All translatable phrases with all translations

### Translation Pipeline

The document translation process:

```
1. Document Upload (PDF/DOCX/TXT/MD)
        ↓
2. Convert to Markdown (using markitdown)
        ↓
3. Extract translatable text fragments
        ↓
4. Translate each fragment in parallel/batches
   (uses the same multi-model translation API)
        ↓
5. Reconstruct documents with translations
        ↓
6. Generate outputs:
   - document_russian.md
   - document_kazakh.md
   - document_original.md
   - translations.json
```

### JSON Export Format

The JSON export contains all translatable phrases:

```json
{
  "document": "example.pdf",
  "format": "pdf",
  "source_language": "en",
  "phrases": [
    {
      "original": "Hello world",
      "russian": "Привет, мир",
      "kazakh": "Сәлем Әлем"
    },
    {
      "original": "Welcome to our application",
      "russian": "Добро пожаловать в наше приложение",
      "kazakh": "Біздің қолданбаға қош келдіңіз"
    }
  ]
}
```

### Features

- **Automatic Text Extraction**: Intelligently extracts translatable text while preserving document structure
- **Parallel Translation**: Fragments are translated in batches for optimal performance
- **Structure Preservation**: Maintains headings, lists, paragraphs, and formatting
- **Real-time Updates**: Status updates every 500ms for live progress tracking
- **Multiple Outputs**: Get translations in multiple formats (MD, JSON)
- **Job Tracking**: Save your Job ID to check status later

### Tips

- **Large Documents**: May take several minutes depending on document length
- **Keep Job ID**: Save your Job ID to check status later or share with others
- **Markdown Output**: All documents are converted to Markdown for consistency
- **Original Preservation**: Download the original (converted to MD) for comparison

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
│   │   ├── models.py       # Pydantic models (incl. document models)
│   │   └── services/
│   │       ├── translator.py          # Translation service
│   │       ├── evaluator.py           # Evaluation service
│   │       └── document_translator.py # Document translation service
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main app with routing
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── TranslationPanel.jsx  # Text translation UI
│   │       └── DocumentPage.jsx      # Document translation UI
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── config.yaml            # Model and translation configuration
├── .env.example          # Example environment variables
├── docker-compose.yml    # Docker Compose configuration (GPU)
├── docker-compose.cpu.yml # Docker Compose configuration (CPU-only)
├── start.sh             # Linux/Mac startup script (auto-detects CUDA)
├── start.bat            # Windows startup script (auto-detects CUDA)
└── README.md            # This file
```

## API Endpoints

### Text Translation

#### POST `/api/translate`

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

### Document Translation

#### POST `/api/documents/upload`

Upload a document for translation.

**Request:** (multipart/form-data)
- `file`: Document file (PDF, DOCX, TXT, MD)
- `source_language`: Source language code ("en" or "zh-TW")

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document uploaded successfully. Translation started.",
  "document_name": "example.pdf",
  "source_language": "en"
}
```

#### GET `/api/documents/jobs/{job_id}/status`

Get the status of a document translation job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "document_name": "example.pdf",
  "source_language": "en",
  "progress": 45.5,
  "total_phrases": 150,
  "translated_phrases": 68,
  "created_at": "2026-01-21T10:30:00Z",
  "completed_at": null,
  "error_message": null
}
```

**Status values:**
- `pending`: Job created, waiting to start
- `processing`: Translation in progress
- `completed`: Translation finished successfully
- `failed`: Translation failed (see error_message)

#### GET `/api/documents/jobs/{job_id}/download/{language}`

Download a translated document.

**Parameters:**
- `language`: One of:
  - `russian`: Russian translation (Markdown)
  - `kazakh`: Kazakh translation (Markdown)
  - `original`: Original document (converted to Markdown)
  - `json`: JSON export with all phrases and translations

**Response:** File download

### System

#### GET `/api/health`

Check API health and available models.

#### GET `/api/models`

Get list of configured models and their status.

For full API documentation, visit http://localhost:8000/api/docs when the system is running.

## Troubleshooting

### KazLLM-8B GGUF File Not Found

If you see this error when starting the system:

```
ERROR: KazLLM-8B GGUF file not found
The KazLLM-8B model is enabled in config.yaml but the GGUF file is missing.
```

You have two options:

**Option 1: Add the GGUF file** (if you have it)

Place the `llama-3.1-kazllm-1.0-8b-q4_k_m.gguf` file in the `TranslatorBK/` directory and run `./start.sh` (or `start.bat` on Windows) again. The script will automatically copy it to Docker.

**Option 2: Disable the model** (if you don't have it)

Edit `config.yaml` and change:

```yaml
- name: kazllm-8b
  enabled: false  # Change from true to false
```

For download instructions with Hugging Face authentication, see [DOWNLOAD_KAZLLM.md](DOWNLOAD_KAZLLM.md).

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
