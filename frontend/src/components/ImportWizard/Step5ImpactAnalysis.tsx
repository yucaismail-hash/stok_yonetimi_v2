// frontend/src/components/ImportWizard/Step5ImpactAnalysis.tsx
import { useState } from 'react';
import { Box, Typography, Paper, Chip, Alert, LinearProgress, Stack, CircularProgress } from '@mui/material';
import { Assessment, AutoAwesome } from '@mui/icons-material';
import { AnalysisImpact } from '../../types/import';

interface Step5ImpactAnalysisProps {
  data: AnalysisImpact | undefined;
  loading: boolean;
}

const analysisLabels: Record<string, string> = {
  forecast: 'Talep Tahmini',
  safety_stock: 'Emniyet Stoğu',
  supplier: 'Tedarikçi',
  simulation: 'Simülasyon',
  backtest: 'Backtest',
};

const analysisColors: Record<string, string> = {
  forecast: '#1976d2',
  safety_stock: '#2e7d32',
  supplier: '#d32f2f',
  simulation: '#9c27b0',
  backtest: '#ed6c02',
};

export default function Step5ImpactAnalysis({ data, loading }: Step5ImpactAnalysisProps) {
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Analiz etkileri hesaplanıyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        Henüz analiz etki analizi yapılmadı.
      </Alert>
    );
  }

  const { analysis_scores, analysis_results, ai_comment, overall_score } = data;
  const isGood = overall_score >= 80;
  const isMedium = overall_score >= 60;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Analysis Impact Assessment
        </Typography>
        <Assessment sx={{ color: '#1f4e79' }} />
      </Box>

      <Paper sx={{ p: 2, bgcolor: '#f8faff', mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Analiz Hazırlık Skoru
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              %{overall_score.toFixed(0)}
            </Typography>
          </Box>
          <Box sx={{ width: '60%' }}>
            <LinearProgress
              variant="determinate"
              value={overall_score}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  bgcolor: isGood ? '#2e7d32' : isMedium ? '#ed6c02' : '#d32f2f',
                },
              }}
            />
          </Box>
        </Box>
      </Paper>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Analiz Bazlı Skorlar
        </Typography>
        <Stack spacing={1}>
          {Object.entries(analysis_scores || {}).map(([key, score]) => (
            <Paper
              key={key}
              sx={{
                p: 1.5,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                border: `1px solid ${analysisColors[key] || '#6b7280'}30`,
                bgcolor: `${analysisColors[key] || '#6b7280'}08`,
                borderRadius: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    bgcolor: analysisColors[key] || '#6b7280',
                  }}
                />
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {analysisLabels[key] || key}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <LinearProgress
                  variant="determinate"
                  value={score}
                  sx={{
                    width: 100,
                    height: 6,
                    borderRadius: 3,
                    bgcolor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: score >= 80 ? '#2e7d32' : score >= 60 ? '#ed6c02' : '#d32f2f',
                    },
                  }}
                />
                <Typography variant="body2" sx={{ fontWeight: 'bold', minWidth: 40 }}>
                  %{score.toFixed(0)}
                </Typography>
              </Box>
            </Paper>
          ))}
        </Stack>
      </Box>

      {ai_comment && (
        <Alert
          severity={isGood ? 'success' : isMedium ? 'warning' : 'error'}
          sx={{ mb: 2 }}
          icon={<AutoAwesome />}
        >
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            🤖 AI Etki Yorumu
          </Typography>
          <Typography variant="body2">{ai_comment}</Typography>
        </Alert>
      )}

      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        Kritik Eksiklikler
      </Typography>

      <Stack spacing={1}>
        {Object.entries(analysis_results || {}).map(([analysis, impacts]) => {
          const criticalMissing = (impacts || []).filter((i: any) => i.status === 'missing' && i.importance === 'Kritik');
          if (criticalMissing.length === 0) return null;

          return (
            <Paper
              key={analysis}
              sx={{
                p: 1.5,
                bgcolor: '#ffebee',
                border: '1px solid #ef9a9a',
                borderRadius: 2,
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#d32f2f' }}>
                {analysisLabels[analysis] || analysis}
              </Typography>
              {criticalMissing.map((item: any, idx: number) => (
                <Typography key={idx} variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  • {item.message}
                </Typography>
              ))}
            </Paper>
          );
        })}
      </Stack>
    </Box>
  );
}