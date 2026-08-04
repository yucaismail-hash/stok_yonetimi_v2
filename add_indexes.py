# add_indexes.py
"""
Index ekleme script'i - DOCUMENT 03 Part 03
"""

import os
import sys  # ✅ EKLENDI
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SQL indeksleri - JSONB için GIN indeksleri düzeltildi
index_sql = """
-- ============================================
-- FOREIGN KEY İNDEKSLERİ
-- ============================================

-- Company FK indeksleri
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_datasets_company_id ON datasets(company_id);
CREATE INDEX IF NOT EXISTS idx_analysis_datasets_company_id ON analysis_datasets(company_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_company_id ON suppliers(company_id);
CREATE INDEX IF NOT EXISTS idx_user_materials_company_id ON user_materials(company_id);
CREATE INDEX IF NOT EXISTS idx_execution_results_company_id ON execution_results(company_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_company_id ON analysis_results(company_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_company_id ON workflow_executions(company_id);
CREATE INDEX IF NOT EXISTS idx_company_learning_memory_company_id ON company_learning_memory(company_id);
CREATE INDEX IF NOT EXISTS idx_user_learning_data_company_id ON user_learning_data(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_id ON audit_logs(company_id);

-- User FK indeksleri
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_datasets_user_id ON analysis_datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_materials_user_id ON user_materials(user_id);
CREATE INDEX IF NOT EXISTS idx_execution_results_user_id ON execution_results(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_user_id ON analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id ON workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_company_learning_memory_user_id ON company_learning_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_user_learning_data_user_id ON user_learning_data(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);

-- Dataset FK indeksleri
CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id ON dataset_versions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_events_dataset_id ON dataset_events(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_validation_results_dataset_id ON dataset_validation_results(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_diff_results_dataset_id ON dataset_diff_results(dataset_id);
CREATE INDEX IF NOT EXISTS idx_execution_cache_dataset_id ON execution_cache(dataset_id);

-- Workflow Execution FK indeksleri
CREATE INDEX IF NOT EXISTS idx_workflow_tasks_workflow_id ON workflow_tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_results_workflow_id ON execution_results(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_metrics_execution_id ON execution_metrics(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_stage_metrics_execution_id ON execution_stage_metrics(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_resource_metrics_execution_id ON execution_resource_metrics(execution_id);

-- ============================================
-- COMPOSITE İNDEKSLER
-- ============================================

CREATE INDEX IF NOT EXISTS idx_datasets_company_created ON datasets(company_id, created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_datasets_company_created ON analysis_datasets(company_id, created_at);
CREATE INDEX IF NOT EXISTS idx_execution_results_company_status ON execution_results(company_id, status);
CREATE INDEX IF NOT EXISTS idx_analysis_results_company_status ON analysis_results(company_id, status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_company_status ON workflow_executions(company_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_created ON audit_logs(company_id, created_at);
CREATE INDEX IF NOT EXISTS idx_security_events_company_severity ON security_events(company_id, severity);

-- ============================================
-- JSONB GIN İNDEKSLERİ (jsonb için düzeltildi)
-- ============================================

-- analysis_results tablosu (data ve ai_summary zaten jsonb)
CREATE INDEX IF NOT EXISTS idx_analysis_results_data_gin ON analysis_results USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_analysis_results_ai_summary_gin ON analysis_results USING GIN (ai_summary);

-- datasets tablosu (diff_result ve affected_skus zaten jsonb)
CREATE INDEX IF NOT EXISTS idx_datasets_diff_result_gin ON datasets USING GIN (diff_result);
CREATE INDEX IF NOT EXISTS idx_datasets_affected_skus_gin ON datasets USING GIN (affected_skus);

-- workflow_executions tablosu (final_result zaten jsonb)
CREATE INDEX IF NOT EXISTS idx_workflow_executions_final_result_gin ON workflow_executions USING GIN (final_result);

-- audit_logs tablosu (event_data zaten jsonb)
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_data_gin ON audit_logs USING GIN (event_data);

-- security_events tablosu (event_data zaten jsonb)
CREATE INDEX IF NOT EXISTS idx_security_events_event_data_gin ON security_events USING GIN (event_data);

"""

def add_indexes():
    """Tüm indeksleri ekler."""
    try:
        with engine.connect() as conn:
            # Her bir indeks statement'ını ayrı ayrı çalıştır
            for statement in index_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
                    conn.commit()
                    logger.info(f"✅ İndeks eklendi: {statement[:60]}...")
        
        logger.info("🎉 Tüm indeksler başarıyla eklendi!")
        return True
        
    except Exception as e:
        logger.error(f"❌ İndeks ekleme hatası: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  STOKONOMI AI - INDEX ADDITION")
    print("  DOCUMENT 03 Part 03")
    print("="*60 + "\n")
    
    success = add_indexes()
    
    if success:
        print("\n✅ İndeksler başarıyla eklendi!")
        sys.exit(0)
    else:
        print("\n❌ İndeks ekleme başarısız oldu!")
        sys.exit(1)