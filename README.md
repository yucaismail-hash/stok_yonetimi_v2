# Stok Yönetim Sistemi v2

API tabanlı, çok kullanıcılı stok optimizasyon ve talep tahmin sistemi.

## Kurulum

1. python -m venv venv
2. source venv/bin/activate (Windows: venv\Scripts\activate)
3. pip install -r requirements.txt
4. PostgreSQL'de stok_db veritabanını oluştur
5. .env dosyasını düzenle
6. uvicorn app.main:app --reload

## API Dokümantasyonu

Çalışırken http://localhost:8000/docs