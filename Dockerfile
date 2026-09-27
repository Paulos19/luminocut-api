# -----------------------------------------------------------------------------
# Dockerfile para FastAPI (Luminocut API) - Otimizado para Easypanel / Docker
# Base Python 3.11 com aceleração ONNX Runtime e cache de modelos pré-instalado
# -----------------------------------------------------------------------------

FROM python:3.11-slim

# Evitar prompts interativos e escrita de arquivos .pyc
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV U2NET_HOME=/root/.u2net

# Instalar dependências de sistema necessárias para ONNX Runtime, OpenCV e Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependências Python e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pré-carregar o modelo principal (isnet-anime) para resposta instantânea no boot
RUN python -c "import rembg; print('[DOCKER BUILD] Baixando modelo isnet-anime...'); rembg.new_session('isnet-anime'); print('[DOCKER BUILD] Modelo carregado!')"

# Copiar código-fonte da aplicação
COPY . .

# Porta padrão de execução
EXPOSE 8000
ENV PORT=8000

# Executar FastAPI com Uvicorn (suporta porta configurada no Easypanel via $PORT ou padrão 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
