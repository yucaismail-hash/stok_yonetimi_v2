# create_new_tables.py
from app.database import engine
from sqlalchemy import inspect, text

def create_new_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        # uploaded_data tablosu
        if 'uploaded_data' not in existing_tables:
            print("📦 uploaded_data tablosu oluşturuluyor...")
            conn.execute(text("""
                CREATE TABLE uploaded_data (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    filename VARCHAR NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_type VARCHAR DEFAULT 'excel',
                    processed_data JSONB DEFAULT '{}',
                    raw_data JSONB DEFAULT '{}',
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    status VARCHAR DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            print("✅ uploaded_data tablosu oluşturuldu.")
        else:
            print("⏩ uploaded_data tablosu zaten mevcut.")
        
        # analysis_results tablosu
        if 'analysis_results' not in existing_tables:
            print("📊 analysis_results tablosu oluşturuluyor...")
            conn.execute(text("""
                CREATE TABLE analysis_results (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    result_type VARCHAR NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    task_id VARCHAR,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            print("✅ analysis_results tablosu oluşturuldu.")
        else:
            print("⏩ analysis_results tablosu zaten mevcut.")
        
        # Index'ler
        print("🔍 Index'ler oluşturuluyor...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analysis_results_result_type 
            ON analysis_results (result_type)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_analysis_results_task_id 
            ON analysis_results (task_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_data_user_id 
            ON uploaded_data (user_id)
        """))
        
        conn.commit()
        print("✅ Tüm işlemler tamamlandı!")

if __name__ == "__main__":
    create_new_tables()