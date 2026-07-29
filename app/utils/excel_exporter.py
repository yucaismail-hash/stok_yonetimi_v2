# app/utils/excel_exporter.py - TAM DOSYA (GÜNCELLENMİŞ)
# 7 Sayfalı Excel Raporu

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import io
import os


class ExcelExporter:
    """Excel raporlama ve dışa aktarma modülü - 7 Sayfa"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def export_bulk_report(
        self, 
        materials_data: List[Dict], 
        learning_rules: List[Dict] = None,
        ai_decision: Dict = None,
        executive_summary: Dict = None
    ) -> io.BytesIO:
        """
        Tüm malzemeler için toplu rapor oluştur - 7 SAYFA
        
        Sayfa 1: Yönetici Özeti
        Sayfa 2: Kritik Ürünler
        Sayfa 3: Tüm Sonuçlar
        Sayfa 4: AI Kararları
        Sayfa 5: İşletme Hafızası (Learning Engine)
        Sayfa 6: Teknik Analiz
        Sayfa 7: AI Açıklamaları
        
        Args:
            materials_data: Malzeme analiz sonuçları listesi
            learning_rules: Learning Engine'den gelen kurallar (opsiyonel)
            ai_decision: AI Decision Engine'den gelen karar (opsiyonel)
            executive_summary: Yönetici özeti (opsiyonel)
        
        Returns:
            io.BytesIO: Excel dosyası
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # ============================================================
            # 📄 SAYFA 1: Yönetici Özeti
            # ============================================================
            self._create_executive_summary_sheet(
                writer, 
                materials_data, 
                executive_summary,
                ai_decision
            )
            
            # ============================================================
            # 📄 SAYFA 2: Kritik Ürünler
            # ============================================================
            self._create_critical_products_sheet(writer, materials_data)
            
            # ============================================================
            # 📄 SAYFA 3: Tüm Sonuçlar
            # ============================================================
            self._create_all_results_sheet(writer, materials_data)
            
            # ============================================================
            # 📄 SAYFA 4: AI Kararları
            # ============================================================
            self._create_ai_decisions_sheet(writer, materials_data)
            
            # ============================================================
            # 📄 SAYFA 5: İşletme Hafızası (Learning Engine)
            # ============================================================
            self._create_learning_memory_sheet(writer, learning_rules)
            
            # ============================================================
            # 📄 SAYFA 6: Teknik Analiz
            # ============================================================
            self._create_technical_analysis_sheet(writer, materials_data)
            
            # ============================================================
            # 📄 SAYFA 7: AI Açıklamaları
            # ============================================================
            self._create_ai_explanations_sheet(writer, materials_data)
        
        output.seek(0)
        return output
    
    # ============================================================
    # 📄 SAYFA 1: Yönetici Özeti
    # ============================================================
    
    def _create_executive_summary_sheet(
        self, 
        writer: pd.ExcelWriter, 
        materials_data: List[Dict],
        executive_summary: Dict = None,
        ai_decision: Dict = None
    ):
        """Sayfa 1: Yönetici Özeti"""
        
        if not materials_data:
            df_empty = pd.DataFrame({'Bilgi': ['Henüz analiz verisi yok']})
            df_empty.to_excel(writer, sheet_name='Yönetici Özeti', index=False)
            return
        
        total = len(materials_data)
        
        # Metrikleri hesapla
        high_risk_count = len([m for m in materials_data if m.get('risk_level') == 'Yüksek'])
        critical_count = len([m for m in materials_data if m.get('risk_score', 0) > 0.7])
        avg_risk = sum(m.get('risk_score', 0) for m in materials_data) / total if total > 0 else 0
        avg_service = sum(m.get('service_level', 95) for m in materials_data) / total if total > 0 else 95
        
        # En riskli grup
        groups = {}
        for m in materials_data:
            group = m.get('group', 'GENEL')
            risk = m.get('risk_score', 0)
            if group not in groups:
                groups[group] = {'count': 0, 'total_risk': 0}
            groups[group]['count'] += 1
            groups[group]['total_risk'] += risk
        
        riskiest_group = max(groups.items(), key=lambda x: x[1]['total_risk'] / x[1]['count'])[0] if groups else '-'
        
        # En önemli problem
        top_problem = ''
        if high_risk_count > total * 0.2:
            top_problem = f'{high_risk_count} ürün yüksek riskli'
        elif critical_count > total * 0.1:
            top_problem = f'{critical_count} ürün kritik seviyede'
        else:
            top_problem = 'Risk seviyesi genel olarak yönetilebilir'
        
        # AI önerisi
        top_recommendation = ''
        if ai_decision:
            top_recommendation = ai_decision.get('explanation', 'Analiz tamamlandı')
        elif high_risk_count > 0:
            top_recommendation = f'{high_risk_count} yüksek riskli ürün için acil aksiyon önerilir'
        else:
            top_recommendation = 'Mevcut politika başarılı, düzenli takip önerilir'
        
        # Özet verisi
        summary_data = {
            'Rapor Tarihi': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'Analiz Edilen Ürün Sayısı': total,
            'Kritik Ürün Sayısı': critical_count,
            'Ortalama Risk Seviyesi': f'{avg_risk:.2f}',
            'Ortalama Servis Seviyesi': f'%{avg_service:.1f}',
            'En Riskli Grup': riskiest_group,
            'En Önemli Problem': top_problem,
            'AI İlk Önerisi': top_recommendation,
            'Yüksek Riskli Ürün': high_risk_count,
            'Orta Riskli Ürün': total - high_risk_count - len([m for m in materials_data if m.get('risk_level') == 'Düşük']),
            'Düşük Riskli Ürün': len([m for m in materials_data if m.get('risk_level') == 'Düşük']),
        }
        
        # AI Yorumu (varsa)
        if executive_summary:
            summary_data['AI Yönetici Özeti'] = executive_summary.get('summary', '')
        
        df_summary = pd.DataFrame([summary_data])
        df_summary.to_excel(writer, sheet_name='Yönetici Özeti', index=False)
        
        # KPI Tablosu
        kpi_data = [
            {'KPI': '📊 Analiz Edilen Ürün', 'Değer': total, 'Durum': '✅'},
            {'KPI': '⚠️ Kritik Ürün', 'Değer': critical_count, 'Durum': '🔴' if critical_count > 5 else '🟡' if critical_count > 2 else '🟢'},
            {'KPI': '📈 Ortalama Risk', 'Değer': f'{avg_risk:.2f}', 'Durum': '🔴' if avg_risk > 0.5 else '🟡' if avg_risk > 0.3 else '🟢'},
            {'KPI': '🎯 Ortalama Servis', 'Değer': f'%{avg_service:.1f}', 'Durum': '🟢' if avg_service > 95 else '🟡' if avg_service > 90 else '🔴'},
            {'KPI': '🏷️ En Riskli Grup', 'Değer': riskiest_group, 'Durum': '⚠️'},
        ]
        df_kpi = pd.DataFrame(kpi_data)
        df_kpi.to_excel(writer, sheet_name='Yönetici Özeti', startrow=3, index=False)
    
    # ============================================================
    # 📄 SAYFA 2: Kritik Ürünler
    # ============================================================
    
    def _create_critical_products_sheet(self, writer: pd.ExcelWriter, materials_data: List[Dict]):
        """Sayfa 2: Kritik Ürünler - Yalnızca yüksek riskli ürünler"""
        
        critical_items = [m for m in materials_data if m.get('risk_level') == 'Yüksek' or m.get('risk_score', 0) > 0.5]
        
        if not critical_items:
            df_empty = pd.DataFrame({'Bilgi': ['Kritik ürün bulunmuyor.']})
            df_empty.to_excel(writer, sheet_name='Kritik Ürünler', index=False)
            return
        
        rows = []
        for m in critical_items:
            rows.append({
                'Malzeme Kodu': m.get('material_code', ''),
                'Malzeme Grubu': m.get('group', ''),
                'Risk Skoru': round(m.get('risk_score', 0), 3),
                'Risk Seviyesi': m.get('risk_level', ''),
                'CV (Değişim Katsayısı)': round(m.get('cv', 0), 4),
                'Zero Ratio': round(m.get('zero_ratio', 0), 4),
                'Pattern': m.get('pattern_label', ''),
                'Önerilen SS': round(m.get('recommended_value', 0), 0),
                'Mevcut SS': round(m.get('current_ss', 0), 0) if m.get('current_ss') else '-',
                'AI Kararı': m.get('ai_decision', {}).get('decision', '-'),
                'Güven Skoru': f"%{int(m.get('ai_decision', {}).get('confidence', 0) * 100)}" if m.get('ai_decision') else '-',
            })
        
        df_critical = pd.DataFrame(rows)
        df_critical.to_excel(writer, sheet_name='Kritik Ürünler', index=False)
    
    # ============================================================
    # 📄 SAYFA 3: Tüm Sonuçlar
    # ============================================================
    
    def _create_all_results_sheet(self, writer: pd.ExcelWriter, materials_data: List[Dict]):
        """Sayfa 3: Tüm Sonuçlar - Detaylı tablo"""
        
        if not materials_data:
            df_empty = pd.DataFrame({'Bilgi': ['Henüz sonuç yok']})
            df_empty.to_excel(writer, sheet_name='Tüm Sonuçlar', index=False)
            return
        
        rows = []
        for m in materials_data:
            row = {
                'Malzeme Kodu': m.get('material_code', ''),
                'Malzeme Grubu': m.get('group', ''),
                'ABC': m.get('abc', '-'),
                'XYZ': m.get('xyz', '-'),
                'Pattern': m.get('pattern_label', ''),
                'CV': round(m.get('cv', 0), 4),
                'Zero Ratio': round(m.get('zero_ratio', 0), 4),
                'Trend': m.get('trend_direction', ''),
                'Mevsimsellik': '✅' if m.get('has_seasonality') else '❌',
                'Aralıklı Talep': '✅' if m.get('is_intermittent') else '❌',
                'Önerilen SS Metodu': m.get('recommended_method_label', ''),
                'Önerilen SS': round(m.get('recommended_value', 0), 0),
                'Risk Skoru': round(m.get('risk_score', 0), 3),
                'Risk Seviyesi': m.get('risk_level', ''),
                'AI Kararı': m.get('ai_decision', {}).get('decision', '-'),
                'Güven': f"%{int(m.get('ai_decision', {}).get('confidence', 0) * 100)}" if m.get('ai_decision') else '-',
            }
            rows.append(row)
        
        df_results = pd.DataFrame(rows)
        df_results.to_excel(writer, sheet_name='Tüm Sonuçlar', index=False)
    
    # ============================================================
    # 📄 SAYFA 4: AI Kararları
    # ============================================================
    
    def _create_ai_decisions_sheet(self, writer: pd.ExcelWriter, materials_data: List[Dict]):
        """Sayfa 4: AI Kararları - Ürün bazında AI kararları"""
        
        if not materials_data:
            df_empty = pd.DataFrame({'Bilgi': ['Henüz AI kararı yok']})
            df_empty.to_excel(writer, sheet_name='AI Kararları', index=False)
            return
        
        rows = []
        for m in materials_data:
            ai_decision = m.get('ai_decision', {})
            
            # Karar metni
            decision_text = ai_decision.get('decision', 'bekleniyor')
            decision_map = {
                'increase_safety_stock': '📈 Emniyet Stoğunu Artır',
                'decrease_safety_stock': '📉 Emniyet Stoğunu Azalt',
                'change_forecast_model': '🔄 Tahmin Modelini Değiştir',
                'review_supplier': '🔍 Tedarikçiyi Gözden Geçir',
                'investigate_variability': '📊 Değişkenliği Araştır',
                'seasonal_adjustment': '🌊 Mevsimsel Ayarla',
                'maintain_current': '✅ Mevcut Durumu Koru',
                'urgent_action': '🚨 Acil Aksiyon',
                'normal_monitoring': '📋 Normal Takip'
            }
            
            rows.append({
                'Malzeme Kodu': m.get('material_code', ''),
                'AI Kararı': decision_map.get(decision_text, decision_text),
                'Öncelik': ai_decision.get('priority', 'medium').upper(),
                'Güven Skoru': f"%{int(ai_decision.get('confidence', 0) * 100)}",
                'Gerekçe': ' | '.join(ai_decision.get('reasons', ['-'])),
                'Beklenen Etki': ai_decision.get('expected_impact', {}).get('stockout_risk', '-'),
                'Sonraki İnceleme': f"{ai_decision.get('next_review_days', 30)} gün",
                'Açıklama': ai_decision.get('explanation', ''),
            })
        
        df_decisions = pd.DataFrame(rows)
        df_decisions.to_excel(writer, sheet_name='AI Kararları', index=False)
    
    # ============================================================
    # 📄 SAYFA 5: İşletme Hafızası (Learning Engine)
    # ============================================================
    
    def _create_learning_memory_sheet(self, writer: pd.ExcelWriter, learning_rules: List[Dict] = None):
        """Sayfa 5: İşletme Hafızası - Learning Engine tarafından öğrenilen davranışlar"""
        
        if not learning_rules:
            df_empty = pd.DataFrame({
                'Bilgi': ['Henüz öğrenilmiş davranış yok.'],
                'Açıklama': ['Analiz yaptıkça AI işletmenizi tanımaya başlayacak.']
            })
            df_empty.to_excel(writer, sheet_name='İşletme Hafızası', index=False)
            return
        
        rows = []
        for rule in learning_rules:
            rows.append({
                'Kural ID': rule.get('rule_id', ''),
                'Kural Adı': rule.get('rule_name', ''),
                'Tip': rule.get('rule_type', ''),
                'Açıklama': rule.get('description', ''),
                'Güven Skoru': f"%{int(rule.get('confidence_score', 0) * 100)}",
                'Kullanım Sayısı': rule.get('usage_count', 0),
                'Doğrulandı': '✅' if rule.get('is_verified') else '⏳',
                'İlk Görülme': rule.get('first_seen_at', ''),
                'Son Görülme': rule.get('last_seen_at', ''),
                'Pattern Data': str(rule.get('pattern_data', {}))[:200],
            })
        
        df_learning = pd.DataFrame(rows)
        df_learning.to_excel(writer, sheet_name='İşletme Hafızası', index=False)
    
    # ============================================================
    # 📄 SAYFA 6: Teknik Analiz
    # ============================================================
    
    def _create_technical_analysis_sheet(self, writer: pd.ExcelWriter, materials_data: List[Dict]):
        """Sayfa 6: Teknik Analiz - CV, Pattern, ABC, XYZ, Forecast, Trend, Seasonality, Lead Time, Zero Ratio"""
        
        if not materials_data:
            df_empty = pd.DataFrame({'Bilgi': ['Henüz teknik analiz verisi yok']})
            df_empty.to_excel(writer, sheet_name='Teknik Analiz', index=False)
            return
        
        rows = []
        for m in materials_data:
            rows.append({
                'Malzeme Kodu': m.get('material_code', ''),
                'CV (Değişim Katsayısı)': round(m.get('cv', 0), 4),
                'Pattern': m.get('pattern_label', ''),
                'ABC': m.get('abc', '-'),
                'XYZ': m.get('xyz', '-'),
                'Forecast Model': m.get('forecast_model_label', ''),
                'Trend': m.get('trend_direction', ''),
                'Trend %': round(m.get('trend_percent', 0), 1),
                'Sezonsallık': m.get('seasonality_label', ''),
                'Sezonsallık Gücü': round(m.get('seasonality_strength', 0), 2),
                'Lead Time': m.get('lead_time_days', '-'),
                'Zero Ratio': round(m.get('zero_ratio', 0), 4),
                'Aralıklı Talep': '✅' if m.get('is_intermittent') else '❌',
                'Risk Skoru': round(m.get('risk_score', 0), 3),
                'Risk Seviyesi': m.get('risk_level', ''),
            })
        
        df_technical = pd.DataFrame(rows)
        df_technical.to_excel(writer, sheet_name='Teknik Analiz', index=False)
    
    # ============================================================
    # 📄 SAYFA 7: AI Açıklamaları
    # ============================================================
    
    def _create_ai_explanations_sheet(self, writer: pd.ExcelWriter, materials_data: List[Dict]):
        """Sayfa 7: AI Açıklamaları - Her ürün için AI'nın ayrıntılı değerlendirmesi"""
        
        if not materials_data:
            df_empty = pd.DataFrame({'Bilgi': ['Henüz AI açıklaması yok']})
            df_empty.to_excel(writer, sheet_name='AI Açıklamaları', index=False)
            return
        
        rows = []
        for m in materials_data:
            ai_decision = m.get('ai_decision', {})
            
            # Nedenler
            reasons = ai_decision.get('reasons', ['-'])
            reasons_text = '\n'.join([f'• {r}' for r in reasons])
            
            rows.append({
                'Malzeme Kodu': m.get('material_code', ''),
                'Malzeme Grubu': m.get('group', ''),
                'AI Kararı': ai_decision.get('decision', 'bekleniyor'),
                'Güven Skoru': f"%{int(ai_decision.get('confidence', 0) * 100)}",
                'Nedenler': reasons_text,
                'Detaylı Açıklama': ai_decision.get('explanation', ''),
                'Beklenen Etki': ai_decision.get('expected_impact', {}).get('stockout_risk', '-'),
                'Önerilen Aksiyon': ai_decision.get('decision', '-'),
                'Sonraki İnceleme': f"{ai_decision.get('next_review_days', 30)} gün",
            })
        
        df_explanations = pd.DataFrame(rows)
        df_explanations.to_excel(writer, sheet_name='AI Açıklamaları', index=False)
    
    # ============================================================
    # 📌 ESKİ FONKSİYONLAR (Uyumluluk için)
    # ============================================================
    
    def export_recommendations(
        self, 
        material_code: str, 
        material_data: Dict,
        simulation_result: Dict, 
        ai_analysis: Dict,
        optimized_params: Dict
    ) -> io.BytesIO:
        """
        Tek malzeme için önerileri Excel olarak dışa aktar (Eski fonksiyon)
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Özet Sayfası
            summary_data = self._create_summary_sheet(
                material_code, material_data, 
                simulation_result, ai_analysis, 
                optimized_params
            )
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # 2. Detaylı Analiz Sayfası
            detail_df = self._create_detail_sheet(
                material_data, simulation_result, 
                ai_analysis, optimized_params
            )
            detail_df.to_excel(writer, sheet_name='Detaylı Analiz', index=False)
            
            # 3. Haftalık Talep Sayfası
            demand_df = self._create_demand_sheet(material_data)
            demand_df.to_excel(writer, sheet_name='Haftalık Talep', index=False)
            
            # 4. Simülasyon Sonuçları Sayfası
            sim_df = self._create_simulation_sheet(simulation_result)
            sim_df.to_excel(writer, sheet_name='Simülasyon Sonuçları', index=False)
            
            # 5. Tedarikçi Bilgileri Sayfası
            supplier_df = self._create_supplier_sheet(material_data)
            if not supplier_df.empty:
                supplier_df.to_excel(writer, sheet_name='Tedarikçi Bilgileri', index=False)
            
            # 6. Aksiyon Planı Sayfası
            action_df = self._create_action_plan_sheet(material_data, optimized_params)
            action_df.to_excel(writer, sheet_name='Aksiyon Planı', index=False)
        
        output.seek(0)
        return output
    
    def _create_summary_sheet(self, material_code: str, material_data: Dict,
                              simulation_result: Dict, ai_analysis: Dict,
                              optimized_params: Dict) -> Dict:
        """Özet sayfası oluştur (Eski)"""
        service_level = simulation_result.get('service_level_actual', 0)
        stockout_prob = np.mean(simulation_result.get('stockout_probability', [0]))
        cvar_95 = simulation_result.get('cvar_95', 0)
        tail_risk = simulation_result.get('tail_risk', 0)
        
        return {
            'Rapor Tarihi': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'Malzeme Kodu': material_code,
            'Malzeme Açıklaması': material_data.get('description', ''),
            'Malzeme Grubu': material_data.get('group', ''),
            'Mevcut Başlangıç Stoku': material_data.get('initial_stock', 0),
            'Önerilen Başlangıç Stoku': optimized_params.get('recommended_initial_stock', 0),
            'Mevcut EOQ': material_data.get('eoq', 0),
            'Önerilen EOQ': optimized_params.get('optimal_eoq', 0),
            'AI Önerilen Safety Stock': ai_analysis.get('ai_ss', 0),
            'Önerilen Safety Stock': optimized_params.get('safety_stock', 0),
            'Önerilen ROP': optimized_params.get('optimal_rop', 0),
            'Servis Seviyesi (Gerçekleşen)': f"{service_level*100:.1f}%",
            'Servis Seviyesi (Hedef)': "95%",
            'Stok Tükenme Olasılığı': f"{stockout_prob*100:.1f}%",
            'CVaR95': round(cvar_95, 2),
            'Tail Risk': round(tail_risk, 2),
            'Patern': ai_analysis.get('pattern', ''),
            'CV (Değişim Katsayısı)': round(ai_analysis.get('cv', 0), 4),
            'Risk Seviyesi': optimized_params.get('risk_level', ''),
            'AI Çarpan': optimized_params.get('pattern_multiplier', 1.0)
        }
    
    def _create_detail_sheet(self, material_data: Dict, simulation_result: Dict,
                            ai_analysis: Dict, optimized_params: Dict) -> pd.DataFrame:
        """Detaylı analiz sayfası oluştur (Eski)"""
        data = []
        
        historical = material_data.get('historical_demand', [])
        if historical:
            non_zero = [d for d in historical if d > 0]
            data.append({
                'Kategori': 'Talep İstatistikleri',
                'Parametre': 'Ortalama Talep',
                'Değer': f"{np.mean(non_zero):.2f}" if non_zero else "0",
                'Birim': 'Adet/Hafta'
            })
            data.append({
                'Kategori': 'Talep İstatistikleri',
                'Parametre': 'Standart Sapma',
                'Değer': f"{np.std(non_zero):.2f}" if non_zero else "0",
                'Birim': 'Adet'
            })
            data.append({
                'Kategori': 'Talep İstatistikleri',
                'Parametre': 'CV (Değişim Katsayısı)',
                'Değer': f"{ai_analysis.get('cv', 0):.4f}",
                'Birim': ''
            })
            data.append({
                'Kategori': 'Talep İstatistikleri',
                'Parametre': 'Sıfır Talep Oranı',
                'Değer': f"{ai_analysis.get('zero_ratio', 0):.4f}",
                'Birim': ''
            })
        
        data.append({
            'Kategori': 'Tedarik Bilgileri',
            'Parametre': 'Lead Time',
            'Değer': f"{material_data.get('lead_time_days', 0)}",
            'Birim': 'Gün'
        })
        data.append({
            'Kategori': 'Tedarik Bilgileri',
            'Parametre': 'Lead Time Talep',
            'Değer': f"{optimized_params.get('lead_time_demand', 0):.2f}",
            'Birim': 'Adet'
        })
        
        if 'simulation_results' in simulation_result:
            sim = simulation_result['simulation_results']
            methods = {
                'Klasik SS': sim.get('classic_ss', 0),
                'Croston SS': sim.get('croston_ss', 0),
                'Syntetos-Boylan SS': sim.get('syntetos_boylan_ss', 0),
                'Bootstrapping SS': sim.get('bootstrapping_ss', 0),
                'ML SS': sim.get('ml_ss', 0),
                'Hybrid SS': sim.get('hybrid_ss', 0)
            }
            for method, value in methods.items():
                data.append({
                    'Kategori': 'SS Metodları',
                    'Parametre': method,
                    'Değer': f"{value:.2f}",
                    'Birim': 'Adet'
                })
        
        return pd.DataFrame(data)
    
    def _create_demand_sheet(self, material_data: Dict) -> pd.DataFrame:
        """Haftalık talep sayfası oluştur (Eski)"""
        historical = material_data.get('historical_demand', [])
        df = pd.DataFrame({
            'Hafta': list(range(1, len(historical) + 1)),
            'Talep': historical
        })
        return df
    
    def _create_simulation_sheet(self, simulation_result: Dict) -> pd.DataFrame:
        """Simülasyon sonuçları sayfası oluştur (Eski)"""
        sim = simulation_result.get('simulation_results', {})
        
        avg_stock = sim.get('avg_stock', [])
        stockout_prob = sim.get('stockout_probability', [])
        expected_shortage = sim.get('expected_shortage', [])
        
        if not avg_stock:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            'Hafta': list(range(1, len(avg_stock) + 1)),
            'Ortalama Stok': avg_stock,
            'Stok Tükenme Olasılığı': stockout_prob,
            'Beklenen Açık': expected_shortage
        })
        return df
    
    def _create_supplier_sheet(self, material_data: Dict) -> pd.DataFrame:
        """Tedarikçi bilgileri sayfası oluştur (Eski)"""
        suppliers = material_data.get('suppliers', [])
        if not suppliers:
            return pd.DataFrame()
        
        rows = []
        for s in suppliers:
            rows.append({
                'Tedarikçi Kodu': s.get('supplier_id', ''),
                'Pay': f"{s.get('share', 0)*100:.1f}%",
                'Açık Bakiye': s.get('open_qty', 0)
            })
        
        return pd.DataFrame(rows)
    
    def _create_action_plan_sheet(self, material_data: Dict, optimized_params: Dict) -> pd.DataFrame:
        """Aksiyon planı sayfası oluştur (Eski)"""
        initial_stock = material_data.get('initial_stock', 0)
        recommended_stock = optimized_params.get('recommended_initial_stock', 0)
        current_eoq = material_data.get('eoq', 0)
        optimal_eoq = optimized_params.get('optimal_eoq', 0)
        safety_stock = optimized_params.get('safety_stock', 0)
        
        actions = []
        
        if recommended_stock > initial_stock:
            actions.append({
                'Sıra': 1,
                'Aksiyon': 'Başlangıç Stok Artırımı',
                'Mevcut': initial_stock,
                'Önerilen': recommended_stock,
                'Artış': recommended_stock - initial_stock,
                'Birim': 'Adet'
            })
        
        if optimal_eoq > current_eoq:
            actions.append({
                'Sıra': 2,
                'Aksiyon': 'EOQ Yükseltme',
                'Mevcut': current_eoq,
                'Önerilen': optimal_eoq,
                'Artış': optimal_eoq - current_eoq,
                'Birim': 'Adet'
            })
        
        if safety_stock > 0:
            actions.append({
                'Sıra': 3,
                'Aksiyon': 'Safety Stock Güncelleme',
                'Mevcut': material_data.get('initial_stock', 0) - optimized_params.get('lead_time_demand', 0),
                'Önerilen': safety_stock,
                'Artış': safety_stock - (material_data.get('initial_stock', 0) - optimized_params.get('lead_time_demand', 0)),
                'Birim': 'Adet'
            })
        
        if not actions:
            actions.append({
                'Sıra': 1,
                'Aksiyon': 'Mevcut Politika Yeterli',
                'Mevcut': 0,
                'Önerilen': 0,
                'Artış': 0,
                'Birim': ''
            })
        
        return pd.DataFrame(actions)