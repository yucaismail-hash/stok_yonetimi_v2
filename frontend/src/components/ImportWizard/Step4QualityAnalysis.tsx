// frontend/src/components/ImportWizard/Step4QualityAnalysis.tsx
// Veri Kalitesi ve Etki Analizi - YENİ TASARIM

import { Box, Typography, Paper, Chip, Alert, Grid, Divider } from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { ValidationResponse } from '../../types/import';

interface Step4QualityAnalysisProps {
  data: ValidationResponse | null;
  loading: boolean;
}

interface ErrorItem {
  sheet: string;
  row?: number;
  column?: string;
  canonical_field?: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  original_value?: any;
  rows?: number[];
}

export default function Step4QualityAnalysis({ data, loading }: Step4QualityAnalysisProps) {
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Veri kalitesi analiz ediliyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return <Alert severity="info">Henüz veri analizi yapılmadı.</Alert>;
  }

  const { data_quality, impact } = data;
  const summary = data_quality?.summary || {};
  const criticalErrors = data_quality?.critical_errors || [];
  const warnings = data_quality?.warnings || [];
  const infoMessages = data_quality?.info_messages || [];
  
  const totalRows = summary.total_rows || 0;
  const totalCritical = summary.total_critical || 0;
  const totalWarnings = summary.total_warnings || 0;
  const totalInfo = summary.total_info || 0;
  const score = summary.score || 0;
  
  const canProceed = data.can_proceed !== false && totalCritical === 0;

  // Hata için etki ve aksiyon üret
  const getErrorImpact = (err: ErrorItem): string => {
    const field = err.canonical_field || err.column || '';
    const impacts: Record<string, string> = {
      'product_code': 'Bu ürün hiçbir analizde yer almayacaktır.',
      'unit_cost': 'EOQ ve maliyet analizleri üretilemeyecektir.',
      'holding_rate': 'Holding Cost hesapları eksik olacaktır.',
      'lead_time_days': 'Emniyet stoğu ve teslim süresi analizleri yapılamayacaktır.',
      'historical_demand': 'Talep tahmini ve simülasyon çalıştırılamayacaktır.',
      'supplier_id': 'Tedarikçi bazlı risk analizi oluşturulamayacaktır.',
      'ontime_rate': 'Tedarikçi performans analizi yapılamayacaktır.',
      'share': 'Tedarikçi paylaşım analizi yapılamayacaktır.',
    };
    return impacts[field] || 'İlgili analizler etkilenecektir.';
  };

  const getErrorAction = (err: ErrorItem): string => {
    const field = err.canonical_field || err.column || '';
    const actions: Record<string, string> = {
      'product_code': 'Excel\'de Ürün Kodu doldurulmalı veya ilgili satırlar silinmelidir.',
      'unit_cost': 'Excel\'de Birim Maliyet sayısal bir değer olarak düzeltilmelidir.',
      'holding_rate': 'Excel\'de Stok Tutma Oranı 0-100 arası bir değer olmalıdır.',
      'lead_time_days': 'Excel\'de Tedarik Süresi pozitif bir sayı olmalıdır.',
      'historical_demand': 'Excel\'de Talep verileri doldurulmalıdır.',
      'supplier_id': 'Excel\'de Tedarikçi Kodu doldurulmalıdır.',
      'ontime_rate': 'Excel\'de Zamanında Teslim Oranı 0-100 arası olmalıdır.',
      'share': 'Excel\'de Tedarik Payı 0-100 arası olmalıdır.',
    };
    return actions[field] || 'Excel dosyasında ilgili alan düzeltilmeli ve yeniden yüklenmelidir.';
  };

  // Hata mesajını temizle
  const getCleanMessage = (err: ErrorItem): string => {
    let msg = err.message || '';
    // "1. satırda Ürün Kodu boş!" -> "Ürün Kodu boş"
    msg = msg.replace(/\d+\.\s*satırda\s*/, '');
    // "(Kapsama: %99.0)" gibi ek bilgileri temizle
    msg = msg.replace(/\s*\([^)]*\)\s*/, '');
    return msg;
  };

  // Hata tipine göre icon
  const getIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      default: return <InfoIcon color="info" />;
    }
  };

  // Hata tipine göre renk
  const getColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#d32f2f';
      case 'warning': return '#ed6c02';
      default: return '#0288d1';
    }
  };

  const renderErrorList = (errors: ErrorItem[], severity: string) => {
    if (!errors || errors.length === 0) {
      return (
        <Alert severity="success" sx={{ mt: 1 }}>
          {severity === 'critical' ? '✅ Kritik hata yok.' :
           severity === 'warning' ? '✅ Uyarı yok.' :
           '✅ Bilgilendirme yok.'}
        </Alert>
      );
    }

    return (
      <Box sx={{ mt: 1 }}>
        {errors.map((err: ErrorItem, idx: number) => {
          const rows = err.rows || (err.row ? [err.row] : []);
          const rowsText = rows.length > 0 ? rows.join(', ') : 'Belirtilmemiş';
          
          return (
            <Paper
              key={idx}
              sx={{
                p: 2,
                mb: 1.5,
                borderLeft: `4px solid ${getColor(severity)}`,
                bgcolor: severity === 'critical' ? '#fff5f5' :
                         severity === 'warning' ? '#fff8e1' : '#f5f9ff',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                {getIcon(severity)}
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {getCleanMessage(err)}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Sheet: <strong>{err.sheet || 'Belirtilmemiş'}</strong>
                    </Typography>
                    {rows.length > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        Satırlar: <strong>{rowsText}</strong>
                      </Typography>
                    )}
                    {err.column && (
                      <Typography variant="caption" color="text.secondary">
                        Kolon: <strong>{err.column}</strong>
                      </Typography>
                    )}
                    {err.original_value && (
                      <Typography variant="caption" color="text.secondary">
                        Değer: <strong>{String(err.original_value)}</strong>
                      </Typography>
                    )}
                  </Box>

                  <Typography variant="body2" sx={{ mt: 1, color: getColor(severity) }}>
                    📌 <strong>Etkisi:</strong> {getErrorImpact(err)}
                  </Typography>
                  
                  {severity === 'critical' && (
                    <Typography variant="body2" sx={{ mt: 0.5, color: '#d32f2f' }}>
                      ✅ <strong>Aksiyon:</strong> {getErrorAction(err)}
                    </Typography>
                  )}
                </Box>
              </Box>
            </Paper>
          );
        })}
      </Box>
    );
  };

  return (
    <Box>
      {/* Özet Kartı */}
      <Paper sx={{ p: 2.5, bgcolor: '#f8faff', mb: 3 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 6, sm: 2.4 }}>
            <Typography variant="caption" color="text.secondary">Toplam Satır</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{totalRows}</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 2.4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ color: '#d32f2f' }}>
              Kritik Hata
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#d32f2f' }}>
              {totalCritical}
            </Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 2.4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ color: '#ed6c02' }}>
              Uyarı
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#ed6c02' }}>
              {totalWarnings}
            </Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 2.4 }}>
            <Typography variant="caption" color="text.secondary" sx={{ color: '#0288d1' }}>
              Bilgilendirme
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#0288d1' }}>
              {totalInfo}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 2.4 }}>
            <Typography variant="caption" color="text.secondary">Veri Kalitesi</Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: score >= 80 ? '#2e7d32' : score >= 60 ? '#ed6c02' : '#d32f2f' }}>
              {score}/100
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* 1. Kritik Hatalar */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#d32f2f', mb: 1 }}>
          🔴 Kritik Hatalar (Devam Edilemez)
        </Typography>
        {renderErrorList(criticalErrors, 'critical')}
      </Box>

      {/* 2. Uyarılar */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#ed6c02', mb: 1 }}>
          🟠 Uyarılar (Devam Edilebilir)
        </Typography>
        {renderErrorList(warnings, 'warning')}
      </Box>

      {/* 3. Bilgilendirme */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#0288d1', mb: 1 }}>
          ℹ️ Bilgilendirme
        </Typography>
        {renderErrorList(infoMessages, 'info')}
      </Box>

      {/* Impact Analizi Özeti */}
      {impact && (
        <Paper sx={{ p: 2, bgcolor: '#f5f9ff', mb: 3 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            📊 Analiz Hazırlık Skorları
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {Object.entries(impact.analysis_scores || {}).map(([key, score]) => {
              const labels: Record<string, string> = {
                forecast: 'Talep Tahmini',
                safety_stock: 'Emniyet Stoğu',
                supplier: 'Tedarikçi',
                simulation: 'Simülasyon',
                backtest: 'Backtest',
              };
              const numScore = typeof score === 'number' ? score : 0;
              const color = numScore >= 80 ? '#2e7d32' : numScore >= 60 ? '#ed6c02' : '#d32f2f';
              return (
                <Chip
                  key={key}
                  label={`${labels[key] || key}: %${numScore.toFixed(0)}`}
                  sx={{ bgcolor: `${color}15`, color: color, fontWeight: 600 }}
                />
              );
            })}
          </Box>
          {impact.ai_comment && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              🤖 {impact.ai_comment}
            </Typography>
          )}
        </Paper>
      )}

      {/* Sonuç Mesajı */}
      <Divider sx={{ my: 2 }} />
      
      {!canProceed ? (
        <Alert severity="error" sx={{ border: '2px solid #d32f2f' }}>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>
            🔴 Bu veri seti analiz için uygun değildir.
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {totalCritical} kritik hata tespit edildi. Lütfen Excel dosyanızı düzeltip yeniden yükleyiniz.
          </Typography>
          <Box sx={{ mt: 1 }}>
            {criticalErrors.slice(0, 3).map((err: ErrorItem, idx: number) => (
              <Typography key={idx} variant="body2" sx={{ color: '#d32f2f' }}>
                • {getCleanMessage(err)} ({err.sheet || 'Temel_Veriler'})
              </Typography>
            ))}
            {criticalErrors.length > 3 && (
              <Typography variant="body2" sx={{ color: '#d32f2f' }}>
                • +{criticalErrors.length - 3} daha kritik hata
              </Typography>
            )}
          </Box>
        </Alert>
      ) : (
        <Alert severity="success" sx={{ border: '2px solid #2e7d32' }}>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>
            🟢 Veri seti analiz için uygundur.
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {totalWarnings > 0 
              ? `${totalWarnings} uyarı bulunmaktadır ancak analiz devam edebilir.`
              : 'Tüm kontroller başarıyla geçildi.'}
          </Typography>
        </Alert>
      )}
    </Box>
  );
}