// frontend/src/components/ImportWizard/Step6Summary.tsx
// Son Onay Ekranı - Final Gate

import { Box, Typography, Paper, Chip, Alert, Grid, Divider, CircularProgress, Button } from '@mui/material';
import { CheckCircle, Warning, Error, AutoAwesome, Lightbulb, Close } from '@mui/icons-material';
import { ValidationResponse } from '../../types/import';

interface Step6SummaryProps {
  data: ValidationResponse | null;
  loading: boolean;
  canProceed: boolean;
  onComplete: () => void;
}

export default function Step6Summary({ data, loading, canProceed, onComplete }: Step6SummaryProps) {
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Özet hazırlanıyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        Henüz özet bilgisi yok.
      </Alert>
    );
  }

  const { file_info, sheet_check, data_quality, impact } = data;
  const overallScore = impact?.overall_score || 0;
  const isGood = overallScore >= 80;
  const isMedium = overallScore >= 60;

  // ============================================================
  // Kritik hataları topla
  // ============================================================
  const criticalErrors: string[] = [];
  
  // Structural errors
  if (data_quality?.structural_errors) {
    data_quality.structural_errors.forEach((err: any) => {
      if (err.severity === 'critical') {
        criticalErrors.push(`🔴 Yapısal: ${err.message}`);
      }
    });
  }
  
  // Missing data (critical)
  if (data_quality?.missing_data) {
    data_quality.missing_data.forEach((err: any) => {
      if (err.severity === 'critical') {
        const coverage = err.coverage_percentage || 0;
        criticalErrors.push(`🔴 Eksik Veri: ${err.message} (Kapsama: %${coverage.toFixed(1)})`);
      }
    });
  }
  
  // Data type errors (critical)
  if (data_quality?.data_type_errors) {
    data_quality.data_type_errors.forEach((err: any) => {
      if (err.severity === 'critical') {
        criticalErrors.push(`🔴 Veri Tipi: ${err.message} (Değer: ${err.original_value})`);
      }
    });
  }
  
  // Business rule errors (critical)
  if (data_quality?.business_rule_errors) {
    data_quality.business_rule_errors.forEach((err: any) => {
      if (err.severity === 'critical') {
        criticalErrors.push(`🔴 İş Kuralı: ${err.message}`);
      }
    });
  }

  const hasCriticalErrors = criticalErrors.length > 0;
  const canCreateDataset = canProceed && !hasCriticalErrors;

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
        Son Onay Ekranı
      </Typography>

      {/* ============================================================
          CAN_PROCEED = FALSE - KRİTİK HATA VAR
          ============================================================ */}
      {!canCreateDataset && (
        <Alert
          severity="error"
          sx={{ mb: 2, border: '2px solid #d32f2f' }}
          icon={<Error />}
        >
          <Typography variant="body1" sx={{ fontWeight: 700, fontSize: '1rem' }}>
            🔴 Dataset oluşturulamıyor!
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Aşağıdaki <strong>{criticalErrors.length}</strong> kritik sorun giderilmelidir:
          </Typography>
          <Box sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {criticalErrors.map((err, idx) => (
                <li key={idx} style={{ fontSize: '0.8rem', color: '#d32f2f', marginBottom: 2 }}>
                  {err}
                </li>
              ))}
            </ul>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            💡 <strong>Öneri:</strong> Geri adımlara dönerek sorunları düzeltin ve "Veri Kalitesi" adımında yeniden doğrulama yapın.
          </Typography>
        </Alert>
      )}

      {/* ============================================================
          CAN_PROCEED = TRUE - HER ŞEY UYGUN
          ============================================================ */}
      {canCreateDataset && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          icon={<CheckCircle />}
        >
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            ✅ Dataset oluşturmak için tüm koşullar sağlanmıştır.
          </Typography>
        </Alert>
      )}

      {/* ============================================================
          GENEL ÖZET BİLGİLERİ
          ============================================================ */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2, bgcolor: '#f8faff', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Dosya Bilgileri
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {file_info?.file_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {file_info?.total_rows} satır, {file_info?.sheet_count} sheet
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2, bgcolor: '#f8faff', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Sheet Durumu
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {sheet_check?.found?.length || 0}/{sheet_check?.results?.length || 0} sheet mevcut
            </Typography>
            {sheet_check?.missing?.length > 0 && (
              <Typography variant="caption" color="error">
                Eksik: {sheet_check.missing.join(', ')}
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2, bgcolor: '#f8faff', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Veri Kalitesi Skoru
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              %{data_quality?.summary?.score?.toFixed(0) || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {data_quality?.summary?.total_structural || 0} yapısal, 
              {data_quality?.summary?.total_business || 0} iş kuralı hatası
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2, bgcolor: '#f8faff', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Analiz Hazırlık
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              %{overallScore.toFixed(0)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {Object.keys(impact?.analysis_scores || {}).length} analiz değerlendirildi
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Divider sx={{ my: 2 }} />

      {/* ============================================================
          ANALİZ BAZLI SKORLAR
          ============================================================ */}
      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        Analiz Bazlı Hazırlık Skorları
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        {Object.entries(impact?.analysis_scores || {}).map(([key, score]) => {
          const labels: Record<string, string> = {
            forecast: 'Talep Tahmini',
            safety_stock: 'Emniyet Stoğu',
            supplier: 'Tedarikçi',
            simulation: 'Simülasyon',
            backtest: 'Backtest',
          };
          const scoreNum = typeof score === 'number' ? score : 0;
          return (
            <Chip
              key={key}
              label={`${labels[key] || key}: %${scoreNum.toFixed(0)}`}
              color={scoreNum >= 80 ? 'success' : scoreNum >= 60 ? 'warning' : 'error'}
              size="medium"
            />
          );
        })}
      </Box>

      {/* ============================================================
          AI YORUMU
          ============================================================ */}
      {impact?.ai_comment && (
        <Alert severity="info" sx={{ mb: 2 }} icon={<AutoAwesome />}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            🤖 AI Etki Yorumu
          </Typography>
          <Typography variant="body2">{impact.ai_comment}</Typography>
        </Alert>
      )}

      {impact?.ai_recommendation && (
        <Alert 
          severity={isGood ? 'success' : 'warning'} 
          sx={{ mb: 2, border: '2px solid', borderColor: isGood ? '#2e7d32' : '#ed6c02' }}
          icon={<Lightbulb />}
        >
          <Typography variant="body2" sx={{ fontWeight: 700 }}>
            💡 Stokonomi AI Önerisi
          </Typography>
          <Typography variant="body2">{impact.ai_recommendation}</Typography>
        </Alert>
      )}

      {/* ============================================================
          DATASET OLUŞTUR BUTONU (canProceed kontrolü)
          ============================================================ */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={onComplete}
          disabled={!canCreateDataset}
          sx={{
            bgcolor: canCreateDataset ? '#1f4e79' : '#9e9e9e',
            '&:hover': { bgcolor: canCreateDataset ? '#1a3d5c' : '#9e9e9e' },
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '0.85rem',
            px: 4,
            py: 1,
          }}
        >
          {canCreateDataset ? '✅ Dataset Oluştur' : '🔴 Dataset Oluşturulamıyor'}
        </Button>
      </Box>

      {/* Bilgi mesajı */}
      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          💡 Dataset oluşturulduktan sonra analizlere başlayabilirsiniz.
          Eksik alanlar varsa, ilgili analizlerde doğruluk kaybı yaşanabilir.
        </Typography>
      </Alert>
    </Box>
  );
}