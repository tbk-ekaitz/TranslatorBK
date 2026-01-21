# ISSAI Specialized Models Integration

This document explains how to use the specialized Kazakh and Russian translation models from ISSAI (Nazarbayev University).

## 🎯 Available ISSAI Models

### 1. **KazLLM-8B** ✅ INTEGRATED
- **Type**: Kazakh National Language Model
- **Size**: 8B parameters (~5GB GGUF Q4_K_M)
- **Best for**: Professional Kazakh and Russian translations with cultural context
- **Integration**: llama.cpp server (GGUF format)
- **Status**: ✅ Fully integrated and ready to use

### 2. **Qolda** ✅ INTEGRATED
- **Type**: Lightweight multimodal model (text + images)
- **Size**: 4.3B parameters
- **Best for**: Fast translations, runs on limited resources
- **Integration**: Docker container
- **Status**: ✅ Fully integrated and ready to use

### 3. **Tilmash** ⚠️ NOT IMPLEMENTED
- **Type**: Specialized translation model (NLLB-based)
- **Size**: ~600M parameters
- **Best for**: Pure translation EN/RU/KK/TR
- **Status**: ⚠️ Requires Hugging Face approval - not implemented yet

---

## 🚀 Quick Start

The system is configured to automatically download and use KazLLM-8B and Qolda.

### Step 1: Start the System

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

The startup script will:
1. Automatically download KazLLM-8B model (~5GB) if not already downloaded
2. Start all Docker services including llama.cpp and Qolda
3. Configure the models in the translation system

### Step 2: Verify Models Are Running

Check that all services are healthy:
```bash
docker compose ps
```

You should see:
- `translator-ollama` - Healthy
- `translator-llamacpp` - Healthy (KazLLM-8B)
- `translator-qolda` - Healthy
- `translator-backend` - Healthy
- `translator-frontend` - Healthy

### Step 3: Test Translation

Access the web interface at http://localhost:3000 and try translating:
- English → Kazakh (will use KazLLM-8B + Qolda + Llama3.1 + Qwen2.5)
- English → Russian (all models)
- Chinese → Kazakh (KazLLM-8B + Qolda + Qwen2.5)

---

## 📦 Manual Model Download (if needed)

If the automatic download fails, you can download KazLLM-8B manually:

**Linux/Mac:**
```bash
cd scripts
./download-kazllm.sh
```

**Windows:**
```bash
cd scripts
download-kazllm.bat
```

This downloads the model into a Docker volume, making it portable.

---

## 🔧 How It Works

### KazLLM-8B Architecture

```
User Request
     ↓
Backend (FastAPI)
     ↓
llama.cpp Server (port 8080)
     ↓
KazLLM-8B GGUF Model (in Docker volume)
     ↓
Translation Response
```

- **Model Location**: Docker volume `translatorbk_kazllm_models`
- **API Endpoint**: http://llamacpp:8080 (internal Docker network)
- **Format**: GGUF Q4_K_M quantization for efficiency

### Qolda Architecture

```
User Request
     ↓
Backend (FastAPI)
     ↓
Qolda Container (port 8081)
     ↓
ISSAI Qolda Model
     ↓
Translation Response
```

- **API Endpoint**: http://qolda:8000 (internal Docker network)
- **External Access**: http://localhost:8081 (if needed for testing)

---

## 🎛️ Configuration

Models are configured in `config.yaml`:

```yaml
models:
  # KazLLM-8B via llama.cpp
  - name: kazllm-8b
    type: llamacpp
    model_id: llama-3.1-kazllm-1.0-8b-q4_k_m
    base_url: http://llamacpp:8080
    weight: 1.6  # Higher weight for specialized model
    enabled: true
    supported_target_languages: ["ru", "kk"]
    supported_source_languages: ["en", "zh-TW"]

  # ISSAI Qolda
  - name: qolda
    type: qolda
    model_id: issai/Qolda
    base_url: http://qolda:8000
    weight: 1.3
    enabled: true
    supported_target_languages: ["ru", "kk"]
    supported_source_languages: ["en", "zh-TW"]
```

### Enabling/Disabling Models

To disable a model, set `enabled: false`:
```yaml
  - name: kazllm-8b
    enabled: false  # Model won't be used
```

Then restart:
```bash
docker compose restart backend
```

---

## 📊 Model Comparison

| Model | Kazakh Quality | Russian Quality | Speed | Memory | Works Offline |
|-------|---------------|-----------------|-------|--------|---------------|
| **KazLLM-8B** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | 8GB | ✅ Yes |
| **Qolda** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Fast | 6GB | ✅ Yes |
| **Llama 3.1** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Fast | 8GB | ✅ Yes |
| **Qwen 2.5** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Fast | 7GB | ✅ Yes |
| **T-pro-it-2.0** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Slow | 20GB | ✅ Yes |

---

## 🐛 Troubleshooting

### KazLLM-8B not starting

1. **Check if model downloaded:**
```bash
docker run --rm -v translatorbk_kazllm_models:/models alpine ls -lh /models
```

You should see `llama-3.1-kazllm-1.0-8b-q4_k_m.gguf` (~5GB).

2. **Re-download model:**
```bash
./scripts/download-kazllm.sh
```

3. **Check llama.cpp logs:**
```bash
docker compose logs llamacpp
```

### Qolda not responding

1. **Check if container is running:**
```bash
docker compose ps qolda
```

2. **View logs:**
```bash
docker compose logs qolda
```

3. **Restart Qolda:**
```bash
docker compose restart qolda
```

### Out of Memory

If you get OOM errors:

1. **Disable heavy models** in `config.yaml`:
```yaml
  - name: t-pro-it-2.0
    enabled: false  # Requires 20GB VRAM
```

2. **Increase Docker resources**:
   - Docker Desktop → Settings → Resources
   - Increase Memory to 16GB+

---

## 🔄 Portability

The entire system is portable. To move to another server:

1. **Export volumes:**
```bash
docker compose down
tar -czf kazllm-models.tar.gz $(docker volume inspect translatorbk_kazllm_models --format '{{ .Mountpoint }}')
tar -czf ollama-models.tar.gz $(docker volume inspect translatorbk_ollama_data --format '{{ .Mountpoint }}')
```

2. **Copy the entire directory:**
```bash
tar -czf TranslatorBK.tar.gz TranslatorBK/
```

3. **On new server:**
```bash
tar -xzf TranslatorBK.tar.gz
cd TranslatorBK
docker compose up -d
```

Models in Docker volumes will be preserved!

---

## 📚 References

- **KazLLM**: https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B
- **Qolda**: https://huggingface.co/issai/Qolda
- **ISSAI**: https://issai.nu.edu.kz/
- **llama.cpp**: https://github.com/ggerganov/llama.cpp

---

## ✨ Benefits of ISSAI Models

1. **Cultural Accuracy**: KazLLM trained on Kazakh cultural context
2. **Language Quality**: Specialized for Kazakh language nuances
3. **Offline Capable**: All models run locally, no internet needed
4. **Free & Open**: CC BY-NC 4.0 license for research/education
5. **Portable**: Fully dockerized, easy to deploy

---

For questions or issues, see the main README.md or create an issue on GitHub.
