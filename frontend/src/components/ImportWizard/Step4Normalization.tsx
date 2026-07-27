// frontend/src/components/ImportWizard/Step4Normalization.tsx
import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Alert,
  Stack,
  CircularProgress,
  Button,
  TextField,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  AutoAwesome,
  CheckCircle,
  Error,
  Edit,
  Save,
  Cancel,
  ExpandMore,
  ExpandLess,
  Check,
  Close,
} from '@mui/icons-material';
import { NormalizationResult } from '../../types/import';

interface Step4NormalizationProps {
  data: NormalizationResult | undefined | null;
  loading: boolean;
  onReValidate?: (corrections: any) => Promise<void>;
  onNext?: () => void;
}

interface CorrectionItem {
  key: string;
  sheet: string;
  row: number;
  column: string;
  original: string;
  suggestion?: string;
  type: 'suggestion' | 'error';
  newValue: string;
}

export default function Step4Normalization({
  data,
  loading,
  onReValidate,
  onNext,
}: Step4NormalizationProps) {
  
  if (data === null || data === undefined) {
    return <Alert severity="info">Henüz veri standardizasyonu yapılmadı.</Alert>;
  }
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    changes: true,
    suggestions: false,
    errors: false,
  });

  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [selectedCorrections, setSelectedCorrections] = useState<
    Record<string, boolean>
  >({});
  const [applying, setApplying] = useState(false);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleManualChange = (key: string, value: string) => {
    setCorrections((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSelectCorrection = (key: string, accepted: boolean) => {
    setSelectedCorrections((prev) => ({
      ...prev,
      [key]: accepted,
    }));
  };

  const handleApplyCorrections = async () => {
    if (Object.keys(corrections).length === 0 && Object.keys(selectedCorrections).length === 0) {
      alert('Düzeltme yapılmamış.');
      return;
    }

    setApplying(true);
    try {
      // Tüm düzeltmeleri birleştir
      const allCorrections: Record<string, any> = {};
      
      // Manuel düzeltmeler
      for (const [key, value] of Object.entries(corrections)) {
        if (value.trim()) {
          allCorrections[key] = value.trim();
        }
      }
      
      // Seçili suggestions (kabul edilenler)
      for (const [key, accepted] of Object.entries(selectedCorrections)) {
        if (accepted) {
          // Suggestion değerini bul
          const suggestion = data?.suggestions?.find((s) => {
            const sKey = `${s.sheet}_${s.row}_${s.column}`;
            return sKey === key;
          });
          if (suggestion) {
            allCorrections[key] = suggestion.suggestion;
          }
        }
      }

      if (Object.keys(allCorrections).length === 0) {
        alert('Düzeltme yapılmamış.');
        setApplying(false);
        return;
      }

      if (onReValidate) {
        await onReValidate(allCorrections);
        setCorrections({});
        setSelectedCorrections({});
      }
    } catch (error) {
      console.error('❌ Düzeltme uygulama hatası:', error);
      alert('Düzeltmeler uygulanırken bir hata oluştu.');
    } finally {
      setApplying(false);
    }
  };

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
    return <Alert severity="info">Henüz veri standardizasyonu yapılmadı.</Alert>;
  }

  // ============================================================
  // ✅ errors array'ini filtrele - duplicate'leri temizle
  // ============================================================
  const getUniqueErrors = (errors: any[]) => {
    if (!errors) return [];
    const seen = new Set();
    return errors.filter(err => {
      const key = `${err.sheet}_${err.row}_${err.column}_${err.value}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  const uniqueErrors = getUniqueErrors(data?.errors || []);

    // ✅ Eğer data varsa ama changes/suggestions/errors boşsa bilgi ver
  const hasNoChanges = !data.changes || data.changes.length === 0;
  const hasNoSuggestions = !data.suggestions || data.suggestions.length === 0;
  const hasNoErrors = !data.errors || data.errors.length === 0;

  if (hasNoChanges && hasNoSuggestions && hasNoErrors) {
    return (
      <Alert severity="success" sx={{ mt: 2 }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
          ✅ Düzeltme gerektiren bir durum yok.
        </Typography>
        <Typography variant="caption">
          Tüm veriler zaten standart formatta. Devam edebilirsiniz.
        </Typography>
      </Alert>
    );
  }

  const {
    changes,
    suggestions,
    errors,
    total_changes,
    total_suggestions,
    total_errors,
  } = data;

  const hasCorrections = Object.keys(corrections).length > 0 || Object.keys(selectedCorrections).length > 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Smart Data Normalization
        </Typography>
        <AutoAwesome sx={{ color: '#1f4e79' }} />
      </Box>

      {/* Özet */}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        <Chip
          icon={<CheckCircle sx={{ fontSize: 14 }} />}
          label={`✅ ${total_changes || 0} otomatik düzeltme`}
          color="success"
          size="small"
          onClick={() => toggleSection('changes')}
        />
        {(total_suggestions || 0) > 0 && (
          <Chip
            icon={<Edit sx={{ fontSize: 14 }} />}
            label={`💡 ${total_suggestions} öneri`}
            color="warning"
            size="small"
            onClick={() => toggleSection('suggestions')}
          />
        )}
        {(total_errors || 0) > 0 && (
          <Chip
            icon={<Error sx={{ fontSize: 14 }} />}
            label={`🔴 ${total_errors} manuel düzeltme gerekli`}
            color="error"
            size="small"
            onClick={() => toggleSection('errors')}
          />
        )}
        {hasCorrections && (
          <Chip
            icon={<Save sx={{ fontSize: 14 }} />}
            label={`${Object.keys(corrections).length + Object.keys(selectedCorrections).filter(k => selectedCorrections[k]).length} düzeltme bekliyor`}
            color="primary"
            size="small"
          />
        )}
      </Box>

      {/* Otomatik Düzeltmeler */}
      <Collapse in={expandedSections.changes} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#2e7d32', mb: 1 }}
          >
            ✅ Otomatik Güvenli Düzeltmeler
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Eski Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Yeni Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Güven</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(changes || []).slice(0, 20).map((change, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{change.sheet}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{change.row || '-'}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem' }}>{change.column}</TableCell>
                    <TableCell sx={{ fontSize: '0.6rem', color: '#d32f2f' }}>
                      {change.original}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.6rem', color: '#2e7d32', fontWeight: 600 }}>
                      {change.new}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={`%${Math.round((change.confidence || 0) * 100)}`}
                        size="small"
                        color={(change.confidence || 0) >= 0.9 ? 'success' : 'warning'}
                        sx={{ height: 18, fontSize: '0.5rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(changes || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(changes || []).length - 20} daha düzeltme
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Smart Suggestions (Kullanıcı Onayı Gerekenler) */}
      <Collapse in={expandedSections.suggestions} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#ed6c02', mb: 1 }}
          >
            💡 Smart Suggestions (İncelemeniz Önerilir)
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#fff3e0' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Mevcut</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Önerilen</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Aksiyon</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(suggestions || []).slice(0, 20).map((suggestion, idx) => {
                  const key = `${suggestion.sheet}_${suggestion.row}_${suggestion.column}`;
                  const isAccepted = selectedCorrections[key] === true;
                  const isRejected = selectedCorrections[key] === false;
                  
                  return (
                    <TableRow key={idx} hover>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{suggestion.sheet}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{suggestion.row || '-'}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{suggestion.column}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem', color: '#d32f2f' }}>
                        {suggestion.original}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.6rem', color: '#2e7d32' }}>
                        {suggestion.suggestion}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Kabul Et">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleSelectCorrection(key, true)}
                              disabled={isAccepted}
                              sx={{ p: 0.5 }}
                            >
                              <Check fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Reddet">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleSelectCorrection(key, false)}
                              disabled={isRejected}
                              sx={{ p: 0.5 }}
                            >
                              <Close fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {isAccepted && (
                            <Chip label="Kabul" size="small" color="success" sx={{ height: 18, fontSize: '0.5rem' }} />
                          )}
                          {isRejected && (
                            <Chip label="Red" size="small" color="error" sx={{ height: 18, fontSize: '0.5rem' }} />
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {(suggestions || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(suggestions || []).length - 20} daha öneri
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Manuel Düzeltme Gerekenler */}
      <Collapse in={expandedSections.errors} timeout="auto" unmountOnExit>
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 600, color: '#d32f2f', mb: 1 }}
          >
            🔴 Manuel Düzeltme Gerekenler
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffebee' }}>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Sheet</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Satır</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Kolon</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Mevcut Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Yeni Değer</TableCell>
                  <TableCell sx={{ fontSize: '0.65rem', fontWeight: 600 }}>Aksiyon</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(uniqueErrors || []).slice(0, 20).map((error, idx) => {
                  const key = `${error.sheet}_${error.row}_${error.column}`;
                  const currentValue = corrections[key] || '';
                  return (
                    <TableRow key={idx}>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{error.sheet}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{error.row || '-'}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem' }}>{error.column}</TableCell>
                      <TableCell sx={{ fontSize: '0.6rem', color: '#d32f2f' }}>
                        {/* ✅ original yerine value veya original_value kullan */}
                        {error.value || error.original_value || '-'}
                      </TableCell>
                      <TableCell>
                        <TextField
                          size="small"
                          placeholder="Yeni değer girin..."
                          value={currentValue}
                          onChange={(e) => handleManualChange(key, e.target.value)}
                          sx={{
                            width: '100%',
                            '& .MuiInputBase-root': { fontSize: '0.7rem' },
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        {currentValue.trim() && (
                          <Chip
                            label="Düzeltildi"
                            size="small"
                            color="success"
                            sx={{ height: 18, fontSize: '0.5rem' }}
                          />
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {(errors || []).length > 20 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', fontSize: '0.6rem', color: '#9e9e9e' }}>
                      +{(errors || []).length - 20} daha manuel düzeltme
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Collapse>

      {/* Apply Buttons */}
      {hasCorrections && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
          <Button
            variant="outlined"
            color="error"
            onClick={() => {
              setCorrections({});
              setSelectedCorrections({});
            }}
            disabled={applying}
            sx={{ textTransform: 'none', fontSize: '0.75rem' }}
          >
            Tümünü Temizle
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleApplyCorrections}
            disabled={applying}
            sx={{
              bgcolor: '#1f4e79',
              '&:hover': { bgcolor: '#1a3d5c' },
              textTransform: 'none',
              fontSize: '0.75rem',
            }}
          >
            {applying ? 'Uygulanıyor...' : `${Object.keys(corrections).length + Object.keys(selectedCorrections).filter(k => selectedCorrections[k]).length} Düzeltmeyi Kaydet ve Yeniden Doğrula`}
          </Button>
        </Box>
      )}

      {/* Bilgi mesajı */}
      {total_errors === 0 && total_suggestions === 0 && total_changes > 0 && (
        <Alert severity="success" sx={{ mt: 2 }}>
          <Typography variant="body2">
            ✅ Tüm düzeltmeler otomatik olarak uygulandı. Devam edebilirsiniz.
          </Typography>
        </Alert>
      )}

      {total_errors === 0 && total_suggestions === 0 && total_changes === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            ℹ️ Düzeltme gerektiren bir durum yok. Devam edebilirsiniz.
          </Typography>
        </Alert>
      )}

      {total_errors > 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="body2">
            ⚠️ {total_errors} manuel düzeltme gerekiyor. Lütfen yukarıdaki tabloyu doldurun ve "Kaydet" butonuna tıklayın.
          </Typography>
        </Alert>
      )}
    </Box>
  );
}