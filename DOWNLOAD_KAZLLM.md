# Downloading KazLLM-8B Model - Authentication Guide

## ⚠️ Problem: 401 Unauthorized Error

If you're getting a `401 Unauthorized` error when trying to download the KazLLM-8B model, it means the model requires Hugging Face authentication.

```
HTTP request sent, awaiting response... 401 Unauthorized
Username/Password Authentication
```

## ✅ Solution: 3 Methods to Download

> **💡 Quick Tip**: After downloading the GGUF file using any method below, simply place it in the `TranslatorBK/` directory and run `./start.sh` (or `start.bat` on Windows). The startup script will automatically copy it to Docker for you!

---

## Method 1: Use Download Script with Token (Easiest)

### Step 1: Get Hugging Face Token
1. Go to https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Name: `kazllm-download`
4. Permission: **Read** (default)
5. Click **"Generate a token"**
6. **Copy the token** (starts with `hf_...`)

### Step 2: Download with Token

**Linux/Mac:**
```bash
cd scripts
./download-kazllm.sh hf_YOUR_TOKEN_HERE
```

**Windows:**
```bash
cd scripts
download-kazllm.bat hf_YOUR_TOKEN_HERE
```

**Example:**
```bash
./download-kazllm.sh hf_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

---

## Method 2: Manual Download with wget

### Step 1: Create Docker Volume
```bash
docker volume create translatorbk_kazllm_models
```

### Step 2: Download with Authentication

Replace `YOUR_HF_TOKEN` with your token from https://huggingface.co/settings/tokens

```bash
docker run --rm \
  -v translatorbk_kazllm_models:/models \
  alpine sh -c "
    apk add --no-cache wget && \
    cd /models && \
    wget --header='Authorization: Bearer YOUR_HF_TOKEN' \
         --progress=bar:force:noscroll \
         --show-progress \
         -O llama-3.1-kazllm-1.0-8b-q4_k_m.gguf.tmp \
         'https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B-GGUF4/resolve/main/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf' && \
    mv llama-3.1-kazllm-1.0-8b-q4_k_m.gguf.tmp llama-3.1-kazllm-1.0-8b-q4_k_m.gguf
  "
```

---

## Method 3: Hugging Face CLI (Recommended for Advanced Users)

### Step 1: Install Hugging Face CLI
```bash
pip install huggingface-hub
```

### Step 2: Login
```bash
huggingface-cli login
```

Paste your token when prompted.

### Step 3: Download Model
```bash
huggingface-cli download \
  issai/LLama-3.1-KazLLM-1.0-8B-GGUF4 \
  llama-3.1-kazllm-1.0-8b-q4_k_m.gguf \
  --local-dir ./kazllm-model
```

### Step 4: Move to Project Directory

**Option A (Recommended - Automatic):**
```bash
# Move the file to TranslatorBK directory
mv ./kazllm-model/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf TranslatorBK/

# Run startup script - it will automatically copy to Docker
cd TranslatorBK
./start.sh  # Linux/Mac or start.bat on Windows
```

**Option B (Manual - Advanced):**
```bash
docker volume create translatorbk_kazllm_models

docker run --rm \
  -v "$(pwd)/kazllm-model:/source" \
  -v translatorbk_kazllm_models:/models \
  alpine cp /source/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf /models/
```

---

## ✅ Verify Installation

After downloading, verify the model is in place:

```bash
docker run --rm -v translatorbk_kazllm_models:/models alpine ls -lh /models
```

Expected output:
```
-rw-r--r--    1 root     root        4.9G Jan 21 10:30 llama-3.1-kazllm-1.0-8b-q4_k_m.gguf
```

---

## 📤 Sharing the Model (Optional)

If you want to share the downloaded model with others:

### Export Model from Docker Volume
```bash
docker run --rm \
  -v translatorbk_kazllm_models:/models \
  -v "$(pwd):/backup" \
  alpine cp /models/llama-3.1-kazllm-1.0-8b-q4_k_m.gguf /backup/
```

This creates `llama-3.1-kazllm-1.0-8b-q4_k_m.gguf` in your current directory (~5GB).

### Import Model (On Another Machine)

If someone shares the GGUF file with you, simply place it in the `TranslatorBK/` directory:

```bash
# Place the file in the project directory
mv llama-3.1-kazllm-1.0-8b-q4_k_m.gguf TranslatorBK/

# Run the startup script - it will automatically copy to Docker
cd TranslatorBK
./start.sh  # Linux/Mac
# or
start.bat   # Windows
```

The startup script will detect the file and automatically copy it to the Docker volume.

---

## 🔧 Troubleshooting

### "Cannot connect to Docker daemon"
- Make sure Docker is running
- On Windows: Start Docker Desktop
- On Linux: `sudo systemctl start docker`

### "No space left on device"
- The model is ~5GB, ensure you have at least 10GB free
- Check: `docker system df`
- Clean: `docker system prune`

### "Download interrupted"
- Just run the download command again
- The script uses `.tmp` files to avoid corruption

### Model downloaded but llama.cpp won't start
1. Check logs: `docker compose logs llamacpp`
2. Verify file: `docker run --rm -v translatorbk_kazllm_models:/models alpine ls -lh /models`
3. Restart service: `docker compose restart llamacpp`

---

## 🚀 Next Steps

After successful download:

1. **Start the system:**
   ```bash
   ./start.sh          # Linux/Mac
   start.bat           # Windows
   ```

2. **Verify all services:**
   ```bash
   ./scripts/verify-setup.sh
   ```

3. **Access the translation interface:**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## 📚 More Information

- **Full documentation:** See `ISSAI_MODELS.md`
- **Model details:** https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B-GGUF4
- **ISSAI website:** https://issai.nu.edu.kz/

---

**File size:** ~5GB
**Format:** GGUF Q4_K_M (quantized)
**License:** CC BY-NC 4.0
**Best for:** Kazakh and Russian translations
