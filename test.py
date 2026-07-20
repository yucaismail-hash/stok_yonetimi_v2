# test.py - GÜNCELLENMİŞ (önce konfigürasyonu göster)

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai import get_llm_service, AIHealthChecker, get_provider_manager
from app.services.ai.config import AIConfig

def test_ai():
    print("=" * 60)
    print("🔍 AI Servis Testi - Gemini + DeepSeek")
    print("=" * 60)
    
    # ✅ ÖNCE KONFİGÜRASYON DURUMUNU GÖSTER
    AIConfig.print_status()
    
    # 1. Health Check
    print("\n📊 Health Check:")
    health = AIHealthChecker()
    result = health.check_all(force=True)
    
    if not result.get("providers"):
        print("❌ Hiçbir provider kaydedilemedi! API Key'leri kontrol et.")
        return
    
    for provider, status in result.get("providers", {}).items():
        available = "✅" if status.get('available') else "❌"
        model_ok = "✅" if status.get('model_accessible') else "❌"
        print(f"  {provider}: {available} Available, {model_ok} Model")
        if status.get("error"):
            print(f"    Hata: {status['error'][:100]}...")
        if status.get("response_time_ms"):
            print(f"    Yanıt süresi: {status['response_time_ms']:.2f} ms")
    
    # 2. LLM Service Test
    print("\n🤖 LLM Service Test:")
    llm = get_llm_service()
    
    test_prompt = """
    Respond with valid JSON only:
    {
        "message": "Hello, I am working!",
        "status": "success"
    }
    """
    
    try:
        response = llm.generate_json(test_prompt)
        print(f"  ✅ Başarılı!")
        print(f"  📝 Yanıt: {response}")
        
        active = llm.get_active_provider()
        print(f"\n  🎯 Aktif Provider: {active}")
        
    except Exception as e:
        print(f"  ❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. İstatistikler
    print("\n📈 Provider İstatistikleri:")
    stats = llm.get_stats()
    for provider, data in stats.items():
        status = "✅ AKTİF" if data.get('is_active') else "⏸️ PASİF"
        success_rate = data['success_rate']
        print(f"  {provider}: {data['success_calls']}/{data['total_calls']} başarılı (%{success_rate:.1f}) {status}")
        if data.get("last_error"):
            print(f"    Son hata: {data['last_error'][:80]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_ai()