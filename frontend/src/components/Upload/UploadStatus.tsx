import {
  Alert,
  AlertTitle,
  Box,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Info,
} from '@mui/icons-material';

interface UploadStatusProps {
  success: boolean;
  message: string;
  summary?: {
    total_materials: number;
    total_weeks: number;
    errors: number;
    has_suppliers?: boolean;
    has_supplier_mapping?: boolean;
    total_suppliers?: number;
  };
  warnings?: string[];
  errors?: string[];
  onClose?: () => void;
}

export default function UploadStatus({
  success,
  message,
  summary,
  warnings = [],
  errors = [],
  onClose,
}: UploadStatusProps) {
  const hasErrors = errors.length > 0;
  const hasWarnings = warnings.length > 0;

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Alert
        severity={success && !hasErrors ? 'success' : hasErrors ? 'error' : 'warning'}
        onClose={onClose}
        sx={{ mb: 2 }}
      >
        <AlertTitle>
          {success && !hasErrors
            ? '✅ Yükleme Başarılı'
            : hasErrors
            ? '❌ Yükleme Başarısız'
            : '⚠️ Yükleme Tamamlandı (Uyarılar Var)'}
        </AlertTitle>
        {message}
      </Alert>

      {/* Özet Bilgiler */}
      {summary && (
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <Chip
            label={`📦 ${summary.total_materials} Malzeme`}
            color="info"
            variant="outlined"
          />
          <Chip
            label={`📅 ${summary.total_weeks} Hafta`}
            color="info"
            variant="outlined"
          />
          {summary.total_suppliers !== undefined && (
            <Chip
              label={`🏭 ${summary.total_suppliers} Tedarikçi`}
              color={summary.total_suppliers > 0 ? 'success' : 'warning'}
              variant="outlined"
            />
          )}
          {summary.has_supplier_mapping !== undefined && (
            <Chip
              label={summary.has_supplier_mapping ? '✅ Tedarikçi Eşleştirme Var' : '⚠️ Tedarikçi Eşleştirme Yok'}
              color={summary.has_supplier_mapping ? 'success' : 'warning'}
              variant="outlined"
            />
          )}
          {summary.errors !== undefined && summary.errors > 0 && (
            <Chip
              label={`❌ ${summary.errors} Hata`}
              color="error"
              variant="outlined"
            />
          )}
        </Box>
      )}

      {/* Hatalar */}
      {hasErrors && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="error" gutterBottom>
            Hatalar:
          </Typography>
          <List dense disablePadding>
            {errors.map((error, index) => (
              <ListItem key={index} sx={{ py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <ErrorIcon color="error" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={error}
                  slotProps={{
                    primary: { variant: 'body2' }
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Uyarılar */}
      {hasWarnings && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="warning" gutterBottom>
            Uyarılar:
          </Typography>
          <List dense disablePadding>
            {warnings.map((warning, index) => (
              <ListItem key={index} sx={{ py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <Warning color="warning" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={warning}
                  slotProps={{
                    primary: { variant: 'body2' }
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Bilgi */}
      {success && !hasErrors && !hasWarnings && (
        <Alert icon={<Info />} severity="info" sx={{ mt: 1 }}>
          Tüm veriler başarıyla yüklendi. Analiz yapmak için ilgili sayfaya geçin.
        </Alert>
      )}
    </Paper>
  );
}