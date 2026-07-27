// frontend/src/components/ImportWizard/Step3DataValidation.tsx
import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Alert,
  LinearProgress,
  Stack,
  CircularProgress,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { DataQualityResult } from '../../types/import';

interface Step3DataValidationProps {
  data: DataQualityResult | undefined;
  loading: boolean;
  onReValidate?: (corrections: any) => Promise<void>;
}

export default function Step3DataValidation({
  data,
  loading,
  onReValidate,
}: Step3DataValidationProps) {
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    structural: true,
    missing: false,
    type: false,
    business: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

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
    return <Alert severity="info">Henüz veri kalitesi kontrolü yapılmadı.</Alert>;
  }

  const {
    summary,
    structural_errors,
    missing_data,
    data_type_errors,
    business_rule_errors,
  } = data;

  const score = summary?.score || 0;
  const isGood = score >= 80;
  const isMedium = score >= 60;

  const structuralCount = structural_errors?.length || 0;
  const missingCount = missing_data?.length || 0;
  const typeCount = data_type_errors?.length || 0;
  const businessCount = business_rule_errors?.length || 0;

  const criticalCount = [
    ...(structural_errors || []).filter((e) => e.severity === 'critical'),
    ...(missing_data || []).filter((e) => e.severity === 'critical'),
    ...(data_type_errors || []).filter((e) => e.severity === 'critical'),
    ...(business_rule_errors || []).filter((e) => e.severity === 'critical'),
  ].length;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical': return '🔴 Kritik';
      case 'warning': return '⚠️ Uyarı';
      default: return 'ℹ️ Bilgi';
    }
  };

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
        {criticalCount > 0 && (
          <Chip
            label={`🔴 ${criticalCount} Kritik Hata`}
            color="error"
            size="small"
          />
        )}
      </Box>

      {/* Skor */}
      <Paper sx={{ p: 2, bgcolor: '#f8faff', mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
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
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                mt: 0.5,
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Kritik: {criticalCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Toplam Hata:{' '}
                {structuralCount + missingCount + typeCount + businessCount}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Özet */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        <Chip
          label={`🔴 Yapısal: ${structuralCount}`}
          color={structuralCount > 0 ? 'error' : 'success'}
          size="small"
          onClick={() => toggleSection('structural')}
          icon={structuralCount > 0 ? <Error /> : <CheckCircle />}
        />
        <Chip
          label={`🟠 Eksik Veri: ${missingCount}`}
          color={missingCount > 0 ? 'warning' : 'success'}
          size="small"
          onClick={() => toggleSection('missing')}
          icon={missingCount > 0 ? <Warning /> : <CheckCircle />}
        />
        <Chip
          label={`🟣 Veri Tipi: ${typeCount}`}
          color={typeCount > 0 ? 'warning' : 'success'}
          size="small"
          onClick={() => toggleSection('type')}
          icon={typeCount > 0 ? <Warning /> : <CheckCircle />}
        />
        <Chip
          label={`🔵 İş Kuralı: ${businessCount}`}
          color={businessCount > 0 ? 'warning' : 'success'}
          size="small"
          onClick={() => toggleSection('business')}
          icon={businessCount > 0 ? <Warning /> : <CheckCircle />}
        />
      </Box>

      {/* Yapısal Hatalar */}
      <Collapse in={expandedSections.structural} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#d32f2f', mb: 1 }}
          >
            🔴 Yapısal Hatalar
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Hata</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Seviye</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(structural_errors || []).map((err, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.sheet}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.column || err.canonical_field}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.message}</TableCell>
                    <TableCell>
                      <Chip
                        label={getSeverityLabel(err.severity)}
                        size="small"
                        color={getSeverityColor(err.severity)}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(!structural_errors || structural_errors.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={4} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#2e7d32' }}>
                      ✅ Yapısal hata yok
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Eksik Veriler */}
      <Collapse in={expandedSections.missing} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#ed6c02', mb: 1 }}
          >
            🟠 Eksik Veriler
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#fff3e0' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Eksik Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kapsama</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Seviye</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(missing_data || []).slice(0, 20).map((err, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.sheet}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.column || err.canonical_field}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>
                      {err.missing_rows}
                      {err.missing_rows_list && err.missing_rows_list.length > 0 && (
                        <Tooltip title={`Eksik satırlar: ${err.missing_rows_list.join(', ')}`}>
                          <Chip
                            label={`${err.missing_rows_list.length} satır`}
                            size="small"
                            sx={{ height: 16, fontSize: '0.45rem', ml: 0.5 }}
                          />
                        </Tooltip>
                      )}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>
                      %{err.coverage_percentage?.toFixed(1) || 0}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getSeverityLabel(err.severity)}
                        size="small"
                        color={getSeverityColor(err.severity)}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(missing_data || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={5} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(missing_data || []).length - 20} daha
                    </TableCell>
                  </TableRow>
                )}
                {(!missing_data || missing_data.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={5} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#2e7d32' }}>
                      ✅ Eksik veri yok
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Veri Tipi Hataları */}
      <Collapse in={expandedSections.type} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#9c27b0', mb: 1 }}
          >
            🟣 Veri Tipi Hataları
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#f3e5f5' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Hata</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Seviye</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(data_type_errors || []).slice(0, 20).map((err, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.sheet}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.row || '-'}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.column || err.canonical_field}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem', color: '#d32f2f' }}>
                      {err.original_value || '-'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.message}</TableCell>
                    <TableCell>
                      <Chip
                        label={getSeverityLabel(err.severity)}
                        size="small"
                        color={getSeverityColor(err.severity)}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(data_type_errors || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(data_type_errors || []).length - 20} daha
                    </TableCell>
                  </TableRow>
                )}
                {(!data_type_errors || data_type_errors.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#2e7d32' }}>
                      ✅ Veri tipi hatası yok
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* İş Kuralı Hataları */}
      <Collapse in={expandedSections.business} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#1976d2', mb: 1 }}
          >
            🔵 İş Kuralı Hataları
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#e3f2fd' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Hata</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Seviye</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(business_rule_errors || []).slice(0, 20).map((err, idx) => (
                  <TableRow key={idx}>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.sheet}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.row || '-'}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.column || err.canonical_field}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem', color: '#d32f2f' }}>
                      {err.original_value || err.value || '-'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{err.message}</TableCell>
                    <TableCell>
                      <Chip
                        label={getSeverityLabel(err.severity)}
                        size="small"
                        color={getSeverityColor(err.severity)}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(business_rule_errors || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(business_rule_errors || []).length - 20} daha
                    </TableCell>
                  </TableRow>
                )}
                {(!business_rule_errors || business_rule_errors.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#2e7d32' }}>
                      ✅ İş kuralı hatası yok
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Kritik Hata Uyarısı */}
      {criticalCount > 0 && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            🔴 {criticalCount} kritik hata tespit edildi.
          </Typography>
          <Typography variant="caption">
            Bu hatalar giderilmeden dataset oluşturulamaz. Lütfen hataları düzeltin ve yeniden doğrulama yapın.
          </Typography>
        </Alert>
      )}

      {criticalCount === 0 && (
        <Alert severity="success" sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            ✅ Kritik hata yok.
          </Typography>
          <Typography variant="caption">
            Veri kalitesi yeterli. Normalizasyon ve etki analizine geçebilirsiniz.
          </Typography>
        </Alert>
      )}
    </Box>
  );
}