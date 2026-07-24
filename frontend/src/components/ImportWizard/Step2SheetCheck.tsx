// frontend/src/components/ImportWizard/Step2SheetCheck.tsx
import { useState, useEffect } from 'react';
import { Box, Typography, Paper, Chip, Alert, Stack, CircularProgress } from '@mui/material';
import { CheckCircle, Error, Warning, Info } from '@mui/icons-material';
import { SheetCheck } from '../../types/import';

interface Step2SheetCheckProps {
  data: SheetCheck | undefined;
  loading: boolean;
  onProceedChange?: (canProceed: boolean) => void;
}

export default function Step2SheetCheck({ data, loading, onProceedChange }: Step2SheetCheckProps) {
  // ✅ İlerleme kontrolü
  const canProceed = data?.success !== false;

  useEffect(() => {
    if (onProceedChange) {
      onProceedChange(canProceed);
    }
  }, [canProceed, onProceedChange]);

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          📋 Sheet'ler kontrol ediliyor...
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Alert severity="info">
        Henüz sheet kontrolü yapılmadı. Önce dosyayı yükleyin.
      </Alert>
    );
  }

  const missingCount = data.missing?.length || 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          📋 Sheet Kontrolü
        </Typography>
        <Chip
          label={data.success ? '✅ Başarılı' : `❌ ${missingCount} Eksik Sheet`}
          color={data.success ? 'success' : 'error'}
          size="small"
        />
      </Box>

      {/* ✅ Uyarı mesajı - Eksik sheet varsa */}
      {!data.success && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          icon={<Error />}
        >
          <Typography variant="body1" sx={{ fontWeight: 600, fontSize: '0.95rem' }}>
            ⚠️ Gerekli Sheet'ler Eksik!
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Aşağıdaki sheet'ler bulunamadı. <strong>Veri dosyanızı düzenleyip tekrar yükleyiniz.</strong>
          </Typography>
          <Box sx={{ mt: 1 }}>
            {data.missing?.map((sheet) => (
              <Chip 
                key={sheet} 
                label={`❌ ${sheet}`} 
                color="error" 
                size="small" 
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            ))}
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            💡 <strong>Öneri:</strong> Excel dosyanızda "{data.missing?.join('", "')}" sheet'lerini oluşturun ve tekrar yükleyin.
          </Typography>
        </Alert>
      )}

      {/* ✅ Bilgi mesajı - Tüm sheet'ler mevcut */}
      {data.success && (
        <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>
          <Typography variant="body2">
            ✅ Tüm gerekli sheet'ler mevcut. Veri kalitesi kontrolüne geçebilirsiniz.
          </Typography>
        </Alert>
      )}

      <Stack spacing={1.5}>
        {data.results?.map((result) => {
          const isRequired = ['Temel_Veriler', 'Tedarikciler', 'Malzeme_Tedarikciler'].includes(result.sheet);
          return (
            <Paper
              key={result.sheet}
              sx={{
                p: 2,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                bgcolor: result.exists ? '#f0f7ff' : '#fff5f5',
                border: `1px solid ${result.exists ? '#d0e0ff' : '#ffcdd2'}`,
                borderRadius: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {result.exists ? (
                  <CheckCircle sx={{ color: '#2e7d32' }} />
                ) : (
                  <Error sx={{ color: '#d32f2f' }} />
                )}
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {result.sheet}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {result.message}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {isRequired && (
                  <Chip
                    label="Zorunlu"
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.55rem' }}
                  />
                )}
                <Chip
                  label={result.exists ? '✅ Mevcut' : '❌ Eksik'}
                  size="small"
                  color={result.exists ? 'success' : 'error'}
                  sx={{ height: 20, fontSize: '0.55rem' }}
                />
              </Box>
            </Paper>
          );
        })}
      </Stack>

      {/* ✅ Eğer ilerleme engellenmişse - Profesyonel mesaj */}
      {!canProceed && (
        <Alert 
          severity="error" 
          sx={{ mt: 2, border: '2px solid #d32f2f' }}
          icon={<Error />}
        >
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            🛑 İlerleme Engellendi
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Eksik sheet'ler nedeniyle veri doğrulama işlemine devam edilemez.
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5, color: '#d32f2f' }}>
            📌 <strong>Yapmanız Gereken:</strong> Excel dosyanıza eksik sheet'leri ekleyin ve dosyayı yeniden yükleyin.
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            ℹ️ Bu işlem veri bütünlüğünü korumak ve analiz doğruluğunu sağlamak için zorunludur.
          </Typography>
        </Alert>
      )}
    </Box>
  );
}