import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import io
import os

class ExcelExporter:
    """Excel raporlama ve dışa aktarma modülü"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def export_recommendations(self, material_code: str, material_data: Dict,
                              simulation_result: Dict, ai_analysis: Dict,
                              optimized_params: Dict) -> io.BytesIO:
        """
        Malzeme için önerileri Excel olarak dışa aktar
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Özet Sayfası
            summary_data = self._create_summary_sheet(material_code, material_data, 
                                                      simulation_result, ai_analysis, 
                                                      optimized_params)
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            # 2. Detaylı Analiz Sayfası
            detail_df = self._create_detail_sheet(material_data, simulation_result, 
                                                  ai_analysis, optimized_params)
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
        """Özet sayfası oluştur"""
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
            'Optimize Edilmiş Safety Stock': optimized_params.get('safety_stock', 0),
            'Mevcut ROP (Tahmini)': optimized_params.get('lead_time_demand', 0) + optimized_params.get('safety_stock', 0),
            'Önerilen ROP': optimized_params.get('optimal_rop', 0),
            'Servis Seviyesi (Gerçekleşen)': f"{service_level*100:.1f}%",
            'Servis Seviyesi (Hedef)': "95%",
            'Stok Tükenme Olasılığı': f"{stockout_prob*100:.1f}%",
            'CVaR95': round(cvar_95, 2),
            'Tail Risk': round(tail_risk, 2),
            'Patern': ai_analysis.get('pattern', ''),
            'CV (Değişim Katsayısı)': round(ai_analysis.get('cv', 0), 4),
            'Tarihsel Veri Haftası': len(material_data.get('historical_demand', [])),
            'Risk Seviyesi': optimized_params.get('risk_level', ''),
            'AI Çarpan': optimized_params.get('pattern_multiplier', 1.0)
        }
    
    def _create_detail_sheet(self, material_data: Dict, simulation_result: Dict,
                            ai_analysis: Dict, optimized_params: Dict) -> pd.DataFrame:
        """Detaylı analiz sayfası oluştur"""
        data = []
        
        # Talep istatistikleri
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
        
        # Lead Time bilgileri
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
        
        # SS Metodları
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
        """Haftalık talep sayfası oluştur"""
        historical = material_data.get('historical_demand', [])
        df = pd.DataFrame({
            'Hafta': list(range(1, len(historical) + 1)),
            'Talep': historical
        })
        return df
    
    def _create_simulation_sheet(self, simulation_result: Dict) -> pd.DataFrame:
        """Simülasyon sonuçları sayfası oluştur"""
        sim = simulation_result.get('simulation_results', {})
        
        # Haftalık verileri al
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
        
        # Sonuç özeti
        summary = {
            'Servis Seviyesi': f"{sim.get('service_level_actual', 0)*100:.1f}%",
            'CVaR95': round(sim.get('cvar_95', 0), 2),
            'Stok Tükenme Toplam': f"{np.sum(sim.get('shortage_paths', [[]])):.2f}"
        }
        
        return df
    
    def _create_supplier_sheet(self, material_data: Dict) -> pd.DataFrame:
        """Tedarikçi bilgileri sayfası oluştur"""
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
        """Aksiyon planı sayfası oluştur"""
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
    
    def export_bulk_report(self, materials_data: List[Dict]) -> io.BytesIO:
        """
        Tüm malzemeler için toplu rapor oluştur
        
        Args:
            materials_data: List of material dicts with analysis results
        
        Returns:
            io.BytesIO: Excel dosyası
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Toplu Özet Sayfası
            summary_rows = []
            for material in materials_data:
                summary_rows.append({
                    'Malzeme Kodu': material.get('code', ''),
                    'Malzeme Grubu': material.get('group', ''),
                    'Mevcut Başlangıç Stoku': material.get('initial_stock', 0),
                    'Önerilen Başlangıç Stoku': material.get('optimized_stock', material.get('initial_stock', 0)),
                    'Mevcut EOQ': material.get('eoq', 0),
                    'Önerilen EOQ': material.get('optimized_eoq', material.get('eoq', 0)),
                    'Safety Stock (AI)': material.get('ai_ss', 0),
                    'Önerilen Safety Stock': material.get('optimized_ss', 0),
                    'Servis Seviyesi (%)': round(material.get('service_level', 0) * 100, 1),
                    'CV (Değişim Katsayısı)': round(material.get('cv', 0), 4),
                    'Pattern': material.get('pattern', ''),
                    'Risk Seviyesi': material.get('risk_level', ''),
                    'Tail Risk': round(material.get('tail_risk', 0), 2),
                    'CVaR95': round(material.get('cvar_95', 0), 2),
                })
            
            df_summary = pd.DataFrame(summary_rows)
            df_summary.to_excel(writer, sheet_name='Toplu Özet', index=False)
            
            # 2. Grup Bazlı Özet Sayfası
            if 'group' in df_summary.columns:
                group_summary = df_summary.groupby('Malzeme Grubu').agg({
                    'Malzeme Kodu': 'count',
                    'Servis Seviyesi (%)': 'mean',
                    'CV (Değişim Katsayısı)': 'mean',
                    'Safety Stock (AI)': 'sum',
                }).reset_index()
                group_summary.columns = ['Malzeme Grubu', 'Malzeme Sayısı', 'Ortalama Servis (%)', 'Ortalama CV', 'Toplam SS']
                group_summary.to_excel(writer, sheet_name='Grup Özeti', index=False)
            
            # 3. Risk Dağılımı Sayfası
            risk_dist = df_summary['Risk Seviyesi'].value_counts().reset_index()
            risk_dist.columns = ['Risk Seviyesi', 'Malzeme Sayısı']
            risk_dist.to_excel(writer, sheet_name='Risk Dağılımı', index=False)
            
            # 4. Pattern Dağılımı Sayfası
            pattern_dist = df_summary['Pattern'].value_counts().reset_index()
            pattern_dist.columns = ['Pattern', 'Malzeme Sayısı']
            pattern_dist.to_excel(writer, sheet_name='Pattern Dağılımı', index=False)
            
            # 5. Aksiyon Gerektiren Malzemeler
            action_needed = df_summary[
                (df_summary['Servis Seviyesi (%)'] < 90) |
                (df_summary['Risk Seviyesi'] == 'YÜKSEK')
            ].copy()
            if not action_needed.empty:
                action_needed['Aksiyon'] = action_needed.apply(
                    lambda row: 'Servis Artır' if row['Servis Seviyesi (%)'] < 90 else 'Risk Azalt',
                    axis=1
                )
                action_needed.to_excel(writer, sheet_name='Aksiyon Gerekenler', index=False)
            
            # 6. Özet İstatistikler
            stats = {
                'Toplam Malzeme': len(df_summary),
                'Ortalama Servis Seviyesi': f"{df_summary['Servis Seviyesi (%)'].mean():.1f}%",
                'Medyan Servis Seviyesi': f"{df_summary['Servis Seviyesi (%)'].median():.1f}%",
                'Min Servis Seviyesi': f"{df_summary['Servis Seviyesi (%)'].min():.1f}%",
                'Max Servis Seviyesi': f"{df_summary['Servis Seviyesi (%)'].max():.1f}%",
                'Ortalama CV': f"{df_summary['CV (Değişim Katsayısı)'].mean():.4f}",
                'Toplam Safety Stock': f"{df_summary['Safety Stock (AI)'].sum():.0f}",
                'Yüksek Risk Malzeme': len(df_summary[df_summary['Risk Seviyesi'] == 'YÜKSEK']),
                'Orta Risk Malzeme': len(df_summary[df_summary['Risk Seviyesi'] == 'ORTA']),
                'Düşük Risk Malzeme': len(df_summary[df_summary['Risk Seviyesi'] == 'DÜŞÜK']),
            }
            df_stats = pd.DataFrame([stats])
            df_stats.to_excel(writer, sheet_name='Özet İstatistikler', index=False)
        
        output.seek(0)
        return output
    
    def _create_summary_sheet(self, material_code: str, material_data: Dict,
                            simulation_result: Dict, ai_analysis: Dict,
                            optimized_params: Dict) -> Dict:
        """Özet sayfası oluştur (Yorumlar ile birlikte)"""
        service_level = simulation_result.get('service_level_actual', 0)
        stockout_prob = np.mean(simulation_result.get('stockout_probability', [0]))
        cvar_95 = simulation_result.get('cvar_95', 0)
        tail_risk = simulation_result.get('tail_risk', 0)
        target_service = 0.95

        # ----- AKILLI YORUMLAR -----
        comments = []

        # 1. Servis Seviyesi Yorumu
        service_gap = target_service - service_level
        if service_gap > 0.05:
            comments.append(
                f"⚠️ Servis seviyesi %{(service_level*100):.1f} ile hedef %95'in altında. "
                f"%{(service_gap*100):.1f} puan artış için Safety Stock'u {optimized_params.get('safety_stock', 0):.0f} birime çıkarın."
            )
        elif service_gap > 0.02:
            comments.append(
                f"📈 Servis seviyesi %{(service_level*100):.1f}, hedefe yakın. "
                f"Safety Stock'u {optimized_params.get('safety_stock', 0):.0f} birime yükselterek %95'e ulaşabilirsiniz."
            )
        else:
            comments.append(
                f"✅ Servis seviyesi %{(service_level*100):.1f} ile hedef %95'te. Mevcut politika başarılı."
            )

        # 2. Stok Tükenme Riski Yorumu
        if stockout_prob > 0.10:
            comments.append(
                f"⚠️ Stok tükenme olasılığı %{(stockout_prob*100):.1f}. "
                f"ROP değerini {optimized_params.get('optimal_rop', 0):.0f} seviyesine çekerek riski azaltın."
            )
        elif stockout_prob > 0.05:
            comments.append(
                f"📊 Stok tükenme olasılığı %{(stockout_prob*100):.1f}, kabul edilebilir seviyede. "
                f"İyileştirme için EOQ'yu {optimized_params.get('optimal_eoq', 0):.0f} olarak güncelleyin."
            )
        else:
            comments.append(
                f"✅ Stok tükenme olasılığı %{(stockout_prob*100):.1f}, düşük seviyede. Mevcut politika yeterli."
            )

        # 3. Tail Risk Yorumu
        if tail_risk > 0.7:
            comments.append(
                f"🚨 Tail Risk {tail_risk:.2f} ile çok yüksek. "
                f"Aşırı talep senaryolarına karşı {optimized_params.get('safety_stock', 0):.0f} birim SS yeterli olmayabilir, "
                f"ek %30 artış önerilir."
            )
        elif tail_risk > 0.4:
            comments.append(
                f"⚠️ Tail Risk {tail_risk:.2f} seviyesinde. "
                f"Kuyruk riski için {optimized_params.get('safety_stock', 0):.0f} birim SS yeterli. "
                f"Talep desenini izlemeye devam edin."
            )
        else:
            comments.append(
                f"✅ Tail Risk {tail_risk:.2f} ile düşük seviyede. Mevcut SS yeterli."
            )

        # 4. CV (Değişkenlik) Yorumu
        cv = ai_analysis.get('cv', 0)
        if cv > 0.7:
            comments.append(
                f"📉 Talep değişkenliği (CV={cv:.2f}) yüksek. "
                f"Bu malzeme için {material_data.get('group', '')} grubu özelinde mevsimsel çarpan kullanılması önerilir."
            )
        elif cv > 0.4:
            comments.append(
                f"📊 Talep değişkenliği (CV={cv:.2f}) orta seviyede. "
                f"Düzenli takip ve aylık SS güncellemesi önerilir."
            )
        else:
            comments.append(
                f"✅ Talep değişkenliği (CV={cv:.2f}) düşük. Mevcut politika devam edebilir."
            )

        # 5. EOQ Yorumu
        current_eoq = material_data.get('eoq', 0)
        optimal_eoq = optimized_params.get('optimal_eoq', 0)
        if optimal_eoq > current_eoq * 1.5:
            comments.append(
                f"📦 EOQ mevcut {current_eoq} birimden {optimal_eoq} birime çıkarılmalı. "
                f"Bu, sipariş maliyetlerini azaltacaktır."
            )
        elif optimal_eoq < current_eoq * 0.5:
            comments.append(
                f"📦 EOQ mevcut {current_eoq} birimden {optimal_eoq} birime düşürülmeli. "
                f"Bu, stok tutma maliyetlerini azaltacaktır."
            )
        else:
            comments.append(
                f"✅ EOQ {current_eoq} birim mevcut seviyede uygun."
            )

        # 6. Genel Öneri (Kullanıcıya Net Aksiyon)
        action_summary = []
        if service_gap > 0.02:
            action_summary.append("Servis seviyesini artır")
        if stockout_prob > 0.05:
            action_summary.append("Stok tükenme riskini azalt")
        if tail_risk > 0.4:
            action_summary.append("Tail riski yönet")
        if cv > 0.7:
            action_summary.append("Mevsimsel çarpan kullan")

        if action_summary:
            action_text = "🎯 **Öncelikli Aksiyonlar:** " + ", ".join(action_summary)
        else:
            action_text = "✅ Mevcut politika başarılı, aksiyon gerekmemektedir."

        comments.append(action_text)

        # Özet verisini oluştur
        summary = {
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

        # Yorumları ayrı bir sütun olarak ekleyelim
        comments_text = "\n".join(comments)
        summary['📌 Yorum ve Öneriler'] = comments_text

        return summary