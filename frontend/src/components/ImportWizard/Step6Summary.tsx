// frontend/src/components/ImportWizard/Step6Summary.tsx - GÜNCELLENMİŞ

import { Box, Typography, Paper, Chip, Alert, Grid, Divider, CircularProgress } from '@mui/material';
import { CheckCircle, Warning, Error, AutoAwesome, Lightbulb } from '@mui/icons-material';
import { ValidationResponse } from '../../types/import';

interface Step6SummaryProps {
  data: ValidationResponse | null;
  loading: boolean;
}

export default function Step6Summary({ data, loading }: Step6SummaryProps) {
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

  const { file_info, sheet_check, data_quality, normalization, impact } = data;
  const overallScore = impact?.overall_score || 0;
  const isGood = overallScore >= 80;
  const isMedium = overallScore >= 60;

  const summaryText = typeof data.summary === 'string' 
    ? data.summary 
    : (data.summary as any)?.summary || 'Dataset hazır!';

  const aiRecommendation = impact?.ai_recommendation || 'Veri seti analiz için hazır.';

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
        Son Onay Ekranı
      </Typography>

      <Alert
        severity={isGood ? 'success' : isMedium ? 'warning' : 'error'}
        sx={{ mb: 2 }}
        icon={<AutoAwesome />}
      >
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {summaryText}
        </Typography>
      </Alert>

      {aiRecommendation && (
        <Alert
          severity={isGood ? 'success' : isMedium ? 'warning' : 'info'}
          sx={{ mb: 2 }}
          icon={<Lightbulb />}
          variant="outlined"
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            🤖 AI Önerisi
          </Typography>
          <Typography variant="body2">
            {aiRecommendation}
          </Typography>
        </Alert>
      )}

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
              Veri Kalitesi
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              %{data_quality?.summary?.score?.toFixed(0) || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {data_quality?.summary?.passed || 0} kontrol başarılı
            </Typography>
            {/* ✅ DÜZELTİLMİŞ business_errors kontrolü */}
            {data_quality?.summary?.business_errors !== undefined && data_quality?.summary?.business_errors > 0 && (
              <Typography variant="caption" color="warning">
                {data_quality?.summary?.business_errors} iş kuralı hatası
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2, bgcolor: '#f8faff', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Otomatik Düzeltme
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {normalization?.total_changes || 0} düzeltme
            </Typography>
            {(normalization?.total_errors || 0) > 0 && (
              <Typography variant="caption" color="warning">
                {normalization.total_errors} manuel düzeltme gerekli
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Divider sx={{ my: 2 }} />

      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        Analiz Hazırlık Skorları
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
          return (
            <Chip
              key={key}
              label={`${labels[key] || key}: %${score.toFixed(0)}`}
              color={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'}
              size="medium"
            />
          );
        })}
        <Chip
          icon={<CheckCircle sx={{ fontSize: 14 }} />}
          label={`Analiz Hazırlık: %${overallScore.toFixed(0)}`}
          color={isGood ? 'success' : isMedium ? 'warning' : 'error'}
          size="medium"
        />
      </Box>

      {impact?.ai_comment && (
        <Alert severity="info" sx={{ mb: 2 }} icon={<AutoAwesome />}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            🤖 AI Etki Yorumu
          </Typography>
          <Typography variant="body2">{impact.ai_comment}</Typography>
        </Alert>
      )}

      {aiRecommendation && (
        <Alert 
          severity={isGood ? 'success' : 'warning'} 
          sx={{ mb: 2, border: '2px solid', borderColor: isGood ? '#2e7d32' : '#ed6c02' }}
          icon={<Lightbulb />}
        >
          <Typography variant="body2" sx={{ fontWeight: 700 }}>
            💡 Stokonomi AI Önerisi
          </Typography>
          <Typography variant="body2">{aiRecommendation}</Typography>
        </Alert>
      )}

      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          💡 Dataset oluşturulduktan sonra analizlere başlayabilirsiniz.
          Eksik alanlar varsa, ilgili analizlerde doğruluk kaybı yaşanabilir.
        </Typography>
      </Alert>
    </Box>
  );
}