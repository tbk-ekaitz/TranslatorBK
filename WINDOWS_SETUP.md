# Running on Windows Native (Not WSL2)

This guide helps you run the translation system on Windows natively instead of WSL2, which often has better GPU support.

## ⚠️ IMPORTANT: Stop WSL2 First

If you've been running this in WSL2, you **MUST** stop it first to avoid port conflicts.

### From Windows PowerShell/CMD (run as Administrator):

```powershell
# Stop all Docker containers in WSL2
wsl -d Ubuntu bash -c "cd ~/TranslatorBK && docker compose down"

# Shut down WSL2 completely
wsl --shutdown
```

This will:
- Stop all Docker containers in WSL2
- Free up ports 3000, 8000, 11434, 8080, 8081
- Shut down the entire WSL2 VM

---

## 📋 Prerequisites

1. **Docker Desktop for Windows** (not Docker in WSL2)
   - Download: https://www.docker.com/products/docker-desktop/
   - During installation, **enable WSL 2 backend** (even though we're running natively)

2. **NVIDIA GPU with latest drivers**
   - Download latest drivers: https://www.nvidia.com/download/index.aspx

3. **Enable GPU in Docker Desktop**
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Ensure "Use the WSL 2 based engine" is enabled
   - GPU should be automatically detected

---

## 🚀 Running on Windows

1. **Open PowerShell or CMD** (normal user, not admin needed)

2. **Navigate to project directory:**
   ```powershell
   cd C:\path\to\TranslatorBK
   ```

3. **Run the startup script:**
   ```cmd
   start.bat
   ```

The script will:
- ✅ Detect your NVIDIA GPU automatically
- ✅ Use GPU-accelerated docker-compose.yml
- ✅ Download required models
- ✅ Start all services

---

## ✅ Verify GPU is Working

After startup, check Ollama logs:

```powershell
docker compose logs ollama | findstr /i "vram gpu"
```

**You should see:**
- `"total vram"="95+ GiB"` ✅ (not "0 B")
- `offloaded 33/33 layers to GPU` ✅

**Monitor GPU usage:**
```powershell
nvidia-smi
```

You should see:
- GPU Memory-Usage increase when models load
- GPU-Util % increase during translation

---

## 🔧 Troubleshooting

### GPU not detected in Windows

1. **Update NVIDIA drivers** to latest version

2. **Check Docker Desktop GPU settings:**
   - Open Docker Desktop
   - Go to Settings → Resources
   - Verify GPU is listed

3. **Test Docker GPU access:**
   ```powershell
   docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
   ```

   If this works, Docker can access GPU ✅

### Port conflicts

If you get port binding errors:

```powershell
# Check what's using the ports
netstat -ano | findstr ":3000 :8000 :11434"

# Stop WSL2 if still running
wsl --shutdown
```

### Containers not starting

```powershell
# View logs
docker compose logs -f

# Restart everything
docker compose down
docker compose up -d
```

---

## 🔄 Switching Between Windows and WSL2

**To use Windows:**
```powershell
# In Windows PowerShell/CMD
cd C:\path\to\TranslatorBK
start.bat
```

**To switch back to WSL2:**
```powershell
# Stop Windows containers first
cd C:\path\to\TranslatorBK
docker compose down

# Start in WSL2
wsl
cd ~/TranslatorBK
./start.sh
```

**Never run both at the same time** - they share the same Docker backend and will conflict.

---

## 📊 Performance Comparison

**Windows Native GPU:**
- ✅ Better GPU detection
- ✅ Direct driver access
- ✅ Usually faster inference
- ✅ More stable

**WSL2 GPU:**
- ⚠️ Requires extra configuration
- ⚠️ May have compatibility issues
- ⚠️ Sometimes slower
- ✅ Easier for Linux tools

**Recommendation:** Use **Windows native** for best GPU performance.
