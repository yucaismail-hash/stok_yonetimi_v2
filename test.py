# test_neon.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Neon bağlantısı başarılı!")
    conn.close()
except Exception as e:
    print(f"❌ Bağlantı hatası: {e}")