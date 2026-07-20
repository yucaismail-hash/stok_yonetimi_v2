# test.py - GÜNCELLENMİŞ

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import AnalysisResult
from app.analysis.ai_summary_engine import AISummaryEngine
from datetime import datetime, timezone
import json

def generate_summary_for_analysis(analysis_id: int):
    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        if not result:
            print(f"❌ Analiz bulunamadı: {analysis_id}")
            return
        
        if result.ai_summary:
            print(f"✅ AI özeti zaten mevcut: {analysis_id}")
            return
        
        print(f"🔄 AI özeti oluşturuluyor: {analysis_id} ({result.result_type})")
        print(f"📊 Veri boyutu: {len(json.dumps(result.data))} karakter")
        
        engine = AISummaryEngine()
        
        # ✅ Hangi modelin kullanıldığını göster
        print(f"🤖 Kullanılan Model: {engine.llm.model_name}")
        print(f"📌 AI Versiyon: {engine.ai_version}")
        
        summary = engine.build_summary(result.result_type, result.data)
        
        result.ai_summary = summary
        result.ai_status = "completed"
        result.ai_version = engine.ai_version
        result.ai_created_at = datetime.now(timezone.utc)
        result.ai_prompt_version = engine.prompt_version
        
        db.commit()
        print(f"✅ AI özeti tamamlandı: {analysis_id}")
        print(f"📝 Manager Summary: {summary.get('manager_summary', '')[:200]}...")
        print(f"📊 Overall Risk: {summary.get('overall_risk', 'Unknown')}")
        print(f"📋 Critical Materials: {summary.get('critical_materials', [])}")
        print(f"💡 Recommended Actions: {summary.get('recommended_actions', [])}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        latest = db.query(AnalysisResult).order_by(AnalysisResult.id.desc()).first()
        if latest:
            print(f"📊 Son analiz ID: {latest.id}, Tip: {latest.result_type}")
            db.close()
            generate_summary_for_analysis(latest.id)
        else:
            print("❌ Hiç analiz bulunamadı.")
            db.close()
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.close()