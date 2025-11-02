# Use imagem Python slim
FROM python:3.11-slim

# Instalar dependências do sistema (Chrome headless + PostgreSQL client)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretório para logs
RUN mkdir -p /var/log

# Comando padrão (executa scheduler que roda diariamente às 11:30)
CMD ["python", "scheduler.py"]
