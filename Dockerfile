# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Çevre değişkenleri
ENV DATABASE_URL=sqlite:///./stok_db.db
ENV SECRET_KEY=docker_secret_key_123456

# Port
EXPOSE 8000

# Uygulamayı çalıştır
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]