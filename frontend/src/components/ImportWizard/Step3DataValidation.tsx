// frontend/src/components/ImportWizard/Step3DataValidation.tsx
import { useState } from 'react';
import { Box, Typography, Paper, Chip, Alert, LinearProgress, Stack, CircularProgress } from '@mui/material';
import { CheckCircle, Error, Warning } from '@mui/icons-material';
import { DataQualityResult } from '../../types/import';

interface Step3DataValidationProps {
  data: DataQualityResult | undefined;
  loading: boolean;
}

export default function Step3DataValidation({ data, loading }: Step3DataValidationProps) {
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Veri kalitesi kontrol ediliyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        Henüz veri kalitesi kontrolü yapılmadı.
      </Alert>
    );
  }

  const { summary, column_checks } = data;
  const score = summary?.score || 0;
  const isGood = score >= 80;
  const isMedium = score >= 60;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Veri Kalitesi
        </Typography>
        <Chip
          label={isGood ? '✅ İyi' : isMedium ? '⚠️ Orta' : '❌ Zayıf'}
          color={isGood ? 'success' : isMedium ? 'warning' : 'error'}
          size="small"
        />
      </Box>

      <Paper sx={{ p: 2, bgcolor: '#f8faff', mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Veri Kalitesi Skoru
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              %{score.toFixed(0)}
            </Typography>
          </Box>
          <Box sx={{ width: '60%' }}>
            <LinearProgress
              variant="determinate"
              value={score}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: '#e0e0e0',
                '& .MuiLinearProgress-bar': {
                  bgcolor: isGood ? '#2e7d32' : isMedium ? '#ed6c02' : '#d32f2f',
                },
              }}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                {summary?.passed || 0} başarılı
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {summary?.failed || 0} hata
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        Kolon Kontrolleri
      </Typography>

      <Stack spacing={1}>
        {(column_checks || []).slice(0, 10).map((check, idx) => (
          <Paper
            key={idx}
            sx={{
              p: 1.5,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              bgcolor: check.status === 'success' ? '#f0f7ff' : '#fff5f5',
              border: `1px solid ${check.status === 'success' ? '#d0e0ff' : '#ffcdd2'}`,
              borderRadius: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              {check.status === 'success' ? (
                <CheckCircle sx={{ color: '#2e7d32', fontSize: 18 }} />
              ) : (
                <Error sx={{ color: '#d32f2f', fontSize: 18 }} />
              )}
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                  {check.sheet} - {check.column}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                  {check.message}
                </Typography>
              </Box>
            </Box>
            <Chip
              label={check.status === 'success' ? '✅ Tamam' : '❌ Eksik'}
              size="small"
              color={check.status === 'success' ? 'success' : 'error'}
              sx={{ height: 20, fontSize: '0.55rem' }}
            />
          </Paper>
        ))}
        {(column_checks || []).length > 10 && (
          <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
            +{(column_checks || []).length - 10} daha kontrol
          </Typography>
        )}
      </Stack>
    </Box>
  );
}