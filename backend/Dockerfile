FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Uploads klasörünü oluştur
RUN mkdir -p uploads

# Port
EXPOSE 8000

# Uvicorn ile çalıştır
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
