#!/bin/bash
# Script para configurar e iniciar el backend real con GPU en el servidor Linux (NVIDIA)

set -e

echo "=== Iniciando Configuracion del Backend xEnglish (NVIDIA GPU) ==="

# 1. Crear entorno virtual
if [ ! -d ".venv" ]; then
    echo "[+] Creando entorno virtual .venv..."
    python -m venv .venv
else
    echo "[*] Entorno virtual .venv ya existe."
fi

# Activar venv
source .venv/bin/activate

# 2. Instalar dependencias basicas
echo "[+] Instalando dependencias base..."
pip install -r requirements.txt

pip install --force-reinstall --no-cache-dir llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# 4. Descargar modelos reales
echo "[+] Verificando/Descargando modelos (GGUF + Piper)..."
python download_models.py

# 5. Configurar .env si no existe
if [ ! -f ".env" ]; then
    echo "[+] Creando archivo .env desde plantilla..."
    cp .env.example .env
fi

# Forzar ejecucion de modelos reales en GPU
export XENGLISH_SKIP_MODELS=0

echo "[+] Levantando servidor Uvicorn con soporte GPU..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
