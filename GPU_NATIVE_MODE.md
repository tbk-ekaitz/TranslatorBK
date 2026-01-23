# GPU Native Mode (WSL2 Workaround)

This mode uses `docker run --gpus all` instead of `docker compose` GPU configuration, which works better in WSL2 environments where `deploy.resources` has issues.

## Problem

In WSL2, Docker Compose's `deploy.resources.reservations.devices` doesn't always properly mount GPU libraries, causing Ollama to detect `"total vram: 0 B"` even though `nvidia-smi` works in containers.

## Solution

The `start-native-gpu.sh` script uses `docker run --gpus all` for GPU services (ollama, llamacpp, qolda) and `docker compose` only for backend/frontend.

---

## When to Use This

Use **GPU Native Mode** if:
- ✅ You're on WSL2
- ✅ `nvidia-smi` works in your terminal
- ✅ `docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi` works
- ❌ But Ollama still shows `"total vram: 0 B"` with regular `docker compose`

---

## Usage

### Start the system:
```bash
./start-native-gpu.sh
```

This will:
1. Verify GPU is accessible with `docker run --gpus`
2. Start Ollama with `docker run --gpus all`
3. Start llamacpp/qolda with `--gpus all` (if enabled)
4. Start backend/frontend with `docker compose`
5. Download required Ollama models
6. Verify GPU detection

### Stop the system:
```bash
./stop-native-gpu.sh
```

Or manually:
```bash
docker stop translator-ollama translator-llamacpp translator-qolda
docker compose down
```

---

## Verify GPU is Working

After starting, check:

```bash
# Should show VRAM detected (NOT "0 B")
docker logs translator-ollama | grep -i vram

# Should show GPU usage increasing
watch -n 1 nvidia-smi

# Check running models
docker exec translator-ollama ollama ps
```

**Expected output:**
```
"total vram"="95.8 GiB"  ✅
offloaded 33/33 layers to GPU  ✅
```

---

## Differences from Regular Mode

| Aspect | Regular Mode (`start.sh`) | GPU Native Mode (`start-native-gpu.sh`) |
|--------|---------------------------|----------------------------------------|
| **GPU Services** | Uses `docker compose` with `deploy.resources` | Uses `docker run --gpus all` |
| **Backend/Frontend** | Uses `docker compose` | Uses `docker compose` |
| **GPU Detection** | May fail in WSL2 | Works reliably |
| **Management** | Single `docker compose down` | Need to stop GPU containers separately |
| **Recommended For** | Windows native, proper Linux | WSL2 |

---

## Troubleshooting

### GPU still shows "0 B VRAM"

Even with `docker run --gpus all`, if this persists:

1. **Check NVIDIA Container Toolkit:**
   ```bash
   sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

2. **Verify Docker can see GPU:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
   ```
   If this fails, the issue is with Docker GPU setup, not the script.

3. **Check Ollama version:**
   ```bash
   docker exec translator-ollama ollama --version
   ```
   Ensure it's a recent version.

### Port conflicts

If ports are already in use:

```bash
# Check what's using the ports
sudo netstat -tulpn | grep -E '3000|8000|11434|8080'

# Stop old containers
docker stop $(docker ps -aq)
```

### Network issues

If containers can't communicate:

```bash
# Recreate network
docker network rm translatorbk_translator-network
./start-native-gpu.sh
```

---

## Managing Models

Models are stored in Docker volumes and persist across restarts:

```bash
# List models
docker exec translator-ollama ollama list

# Add new model
docker exec translator-ollama ollama pull model-name

# Remove model
docker exec translator-ollama ollama rm model-name

# Remove ALL data (warning: deletes models)
docker volume rm translatorbk_ollama_data translatorbk_kazllm_models
```

---

## Performance Monitoring

Monitor GPU usage during translation:

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Check Ollama GPU layers
docker logs translator-ollama | grep -i "offload"

# Monitor all containers
docker stats translator-ollama translator-backend translator-frontend
```

---

## Reverting to Regular Mode

To try regular Docker Compose mode again:

```bash
# Stop GPU native mode
./stop-native-gpu.sh

# Start regular mode
./start.sh
```

The regular mode will work if you properly configure NVIDIA Container Toolkit.

---

## Why This Works

The issue is that `docker compose` in WSL2 doesn't always properly configure the GPU runtime when using `deploy.resources`. However, `docker run --gpus all` uses a different code path that works more reliably.

By separating GPU services (using `docker run`) from regular services (using `docker compose`), we get the best of both worlds:
- ✅ Reliable GPU access for AI models
- ✅ Easy management of backend/frontend with docker compose
- ✅ All services on the same network and can communicate
