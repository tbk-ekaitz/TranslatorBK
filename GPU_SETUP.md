# GPU Setup Guide

This guide helps you configure GPU acceleration for the translation system.

## Quick Test

Run the GPU test script to check if everything is configured correctly:

```bash
./test-gpu.sh
```

## Prerequisites

### For Linux/WSL2:

1. **NVIDIA GPU** with CUDA support
2. **NVIDIA drivers** installed (version 535+ recommended)
3. **Docker** with GPU support
4. **NVIDIA Container Toolkit** installed

## Installation Steps

### 1. Verify GPU is Detected

```bash
nvidia-smi
```

You should see your GPU listed with memory information.

### 2. Install NVIDIA Container Toolkit

#### For Ubuntu/Debian (including WSL2):

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install the toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use the NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker
sudo systemctl restart docker
```

#### For WSL2 Specific:

If using WSL2 on Windows:

1. Install latest NVIDIA drivers in Windows (not in WSL)
2. Update WSL2 kernel: `wsl --update`
3. Follow Ubuntu installation steps above in WSL2

### 3. Test Docker GPU Access

```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

If this works, Docker can access your GPU!

### 4. Restart Translation Services

```bash
# Stop current services
docker compose down

# Start with GPU support
./start.sh
```

## Verification

After restarting, check Ollama logs to verify GPU is being used:

```bash
docker compose logs ollama | grep -i "gpu\|cuda\|nvidia"
```

You should see messages about GPU detection and VRAM allocation, NOT "entering low vram mode" or "total vram: 0 B".

## Troubleshooting

### Ollama shows "total vram: 0 B"

This means the container isn't seeing the GPU. Try:

1. Run `./test-gpu.sh` to diagnose the issue
2. Verify NVIDIA Container Toolkit is installed: `nvidia-ctk --version`
3. Check Docker daemon configuration: `cat /etc/docker/daemon.json`
4. Restart Docker: `sudo systemctl restart docker`
5. Recreate containers: `docker compose down && docker compose up -d`

### "Could not initialize CUDA"

- Update NVIDIA drivers to latest version
- Verify CUDA compatibility: `nvidia-smi` shows CUDA version
- Check container image supports your CUDA version

### WSL2: "nvidia-smi not found"

- Install NVIDIA drivers in Windows (not WSL)
- Update WSL kernel: `wsl --update` (in PowerShell/CMD)
- Restart WSL: `wsl --shutdown` then restart

## Performance Monitoring

Monitor GPU usage while translating:

```bash
watch -n 1 nvidia-smi
```

You should see:
- GPU utilization % increase during translation
- Memory usage increase when models load
- Temperature increase under load

## CPU Fallback

If GPU cannot be configured, the system automatically falls back to CPU mode using `docker-compose.cpu.yml`. Performance will be slower but functionality remains intact.
