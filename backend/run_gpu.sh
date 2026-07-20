#!/bin/bash
# Script optimizado para iniciar el backend real con GPU en el servidor Linux (NVIDIA)

set -e

echo "=== Iniciando Backend xEnglish (NVIDIA GPU) ==="

# 1. Configurar entorno virtual e instalar solo si no existe
if [ ! -d ".venv" ]; then
    echo "[+] No se encontro .venv. Iniciando instalacion completa..."
    python -m venv .venv
    source .venv/bin/activate
    
    echo "[+] Instalando dependencias base..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "[+] Instalando llama-cpp-python precompilado para CUDA 12.4..."
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
else
    echo "[*] Entorno .venv detectado. Activando..."
    source .venv/bin/activate
fi

# 2. Descargar o verificar modelos reales
echo "[+] Verificando modelos (GGUF + Piper)..."
python download_models.py

# 3. Configurar .env si no existe
if [ ! -f ".env" ]; then
    echo "[+] Creando archivo .env desde plantilla..."
    cp .env.example .env
fi

# Forzar ejecucion de modelos reales en GPU
export XENGLISH_SKIP_MODELS=0

echo "[+] Levantando servidor Uvicorn con soporte GPU..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
