// frontend/src/components/ImportWizard/Step4Normalization.tsx
import { useState } from 'react';
import { Box, Typography, Paper, Chip, Alert, Stack, CircularProgress } from '@mui/material';
import { AutoAwesome, CheckCircle, Error, Edit } from '@mui/icons-material';
import { NormalizationResult } from '../../types/import';

interface Step4NormalizationProps {
  data: NormalizationResult | undefined;
  loading: boolean;
}

export default function Step4Normalization({ data, loading }: Step4NormalizationProps) {
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Veri standardizasyonu yapılıyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        Henüz veri standardizasyonu yapılmadı.
      </Alert>
    );
  }

  const { changes, suggestions, errors, total_changes, total_suggestions, total_errors } = data;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Smart Data Normalization
        </Typography>
        <AutoAwesome sx={{ color: '#1f4e79' }} />
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Chip
          icon={<CheckCircle sx={{ fontSize: 14 }} />}
          label={`${total_changes || 0} otomatik düzeltme`}
          color="success"
          size="small"
        />
        {(total_suggestions || 0) > 0 && (
          <Chip
            icon={<Edit sx={{ fontSize: 14 }} />}
            label={`${total_suggestions} öneri`}
            color="warning"
            size="small"
          />
        )}
        {(total_errors || 0) > 0 && (
          <Chip
            icon={<Error sx={{ fontSize: 14 }} />}
            label={`${total_errors} manuel düzeltme gerekli`}
            color="error"
            size="small"
          />
        )}
      </Box>

      {(changes || []).length > 0 && (
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Otomatik Düzeltmeler
        </Typography>
      )}

      <Stack spacing={1}>
        {(changes || []).slice(0, 10).map((change, idx) => (
          <Paper
            key={idx}
            sx={{
              p: 1.5,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              bgcolor: '#e8f5e9',
              border: '1px solid #a5d6a7',
              borderRadius: 2,
            }}
          >
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                {change.sheet} - {change.column}
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                <span style={{ color: '#d32f2f' }}>{change.original}</span>
                {' → '}
                <span style={{ color: '#2e7d32', fontWeight: 600 }}>{change.new}</span>
              </Typography>
            </Box>
            <Chip
              label={`%${Math.round((change.confidence || 0) * 100)} güven`}
              size="small"
              color={(change.confidence || 0) >= 0.9 ? 'success' : 'warning'}
              sx={{ height: 20, fontSize: '0.5rem' }}
            />
          </Paper>
        ))}
        {(changes || []).length > 10 && (
          <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
            +{(changes || []).length - 10} daha düzeltme
          </Typography>
        )}
      </Stack>

      {(suggestions || []).length > 0 && (
        <>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
            Smart Suggestions (İncelemeniz Önerilir)
          </Typography>
          <Stack spacing={1}>
            {(suggestions || []).slice(0, 5).map((suggestion, idx) => (
              <Paper
                key={idx}
                sx={{
                  p: 1.5,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  bgcolor: '#fff3e0',
                  border: '1px solid #ffcc80',
                  borderRadius: 2,
                }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                    {suggestion.sheet} - {suggestion.column}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                    {suggestion.suggestion}
                  </Typography>
                </Box>
                <Chip
                  label={`%${Math.round((suggestion.confidence || 0) * 100)} güven`}
                  size="small"
                  color="warning"
                  sx={{ height: 20, fontSize: '0.5rem' }}
                />
              </Paper>
            ))}
          </Stack>
        </>
      )}

      {(errors || []).length > 0 && (
        <>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
            Manuel Düzeltme Gerekenler
          </Typography>
          <Stack spacing={1}>
            {(errors || []).slice(0, 5).map((error, idx) => (
              <Paper
                key={idx}
                sx={{
                  p: 1.5,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  bgcolor: '#ffebee',
                  border: '1px solid #ef9a9a',
                  borderRadius: 2,
                }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                    {error.sheet} - {error.column}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#d32f2f' }}>
                    {error.message}
                  </Typography>
                </Box>
                <Chip
                  label="Manuel Düzelt"
                  size="small"
                  color="error"
                  sx={{ height: 20, fontSize: '0.5rem' }}
                />
              </Paper>
            ))}
          </Stack>
        </>
      )}
    </Box>
  );
}