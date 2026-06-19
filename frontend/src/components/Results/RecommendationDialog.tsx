// src/components/Results/RecommendationDialog.tsx
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  Grid,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Alert,
  Stack,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  TrendingUp,
  TrendingDown,
  Download,
  Schedule,
  Close,
  Lightbulb,
} from '@mui/icons-material';

interface RecommendationDialogProps {
  open: boolean;
  onClose: () => void;
  materialCode: string;
  materialData: any;
  optimizedParams: any;
  simulationResult: any;
  onExport: () => void;
  onSchedule: () => void;
}

export default function RecommendationDialog({
  open,
  onClose,
  materialCode,
  materialData,
  optimizedParams,
  simulationResult,
  onExport,
  onSchedule,
}: RecommendationDialogProps) {
  const initialStock = materialData?.initial_stock || 0;
  const recommendedStock = optimizedParams?.recommended_initial_stock || 0;
  const currentEoq = materialData?.eoq || 0;
  const optimalEoq = optimizedParams?.optimal_eoq || 0;
  const safetyStock = optimizedParams?.safety_stock || 0;
  const serviceLevel = simulationResult?.service_level_actual || 0;
  const riskLevel = optimizedParams?.risk_level || '';

  const actions = [
    {
      id: 1,
      title: 'Başlangıç Stok Artırımı',
      current: initialStock,
      recommended: recommendedStock,
      change: recommendedStock - initialStock,
      unit: 'Adet',
      icon: <TrendingUp />,
    },
    {
      id: 2,
      title: 'EOQ Yükseltme',
      current: currentEoq,
      recommended: optimalEoq,
      change: optimalEoq - currentEoq,
      unit: 'Adet',
      icon: <TrendingUp />,
    },
    {
      id: 3,
      title: 'Safety Stock Güncelleme',
      current: initialStock - (optimizedParams?.lead_time_demand || 0),
      recommended: safetyStock,
      change: safetyStock - (initialStock - (optimizedParams?.lead_time_demand || 0)),
      unit: 'Adet',
      icon: <Lightbulb />,
    },
  ];

  const getStatusColor = (change: number) => {
    if (change > 0) return 'success';
    if (change < 0) return 'error';
    return 'warning';
  };

  const getStatusLabel = (change: number) => {
    if (change > 0) return 'Artırılmalı';
    if (change < 0) return 'Azaltılabilir';
    return 'Yeterli';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 3 },
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={1}>
            <Lightbulb color="warning" />
            <Typography variant="h6" fontWeight="bold">
              Stok Optimizasyon Önerileri
            </Typography>
          </Box>
          <Chip
            label={riskLevel || 'Orta'}
            color={riskLevel === 'DÜŞÜK' ? 'success' : riskLevel === 'YÜKSEK' ? 'error' : 'warning'}
            size="small"
          />
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {/* Malzeme Bilgisi */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
          <Typography variant="body2" color="info.dark">
            <strong>Malzeme:</strong> {materialCode} - {materialData?.description}
          </Typography>
          <Typography variant="body2" color="info.dark">
            <strong>Grup:</strong> {materialData?.group} |{' '}
            <strong>Servis Seviyesi:</strong> {(serviceLevel * 100).toFixed(1)}%
          </Typography>
        </Box>

        {/* Pay Değişim Aralığı */}
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            🔄 Tedarikçi Pay Değişim Aralığı
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Chip label="Min %2" size="small" color="info" />
            <Box sx={{ flex: 1, height: 8, bgcolor: 'grey.300', borderRadius: 4 }}>
              <Box
                sx={{
                  width: '50%',
                  height: '100%',
                  bgcolor: 'primary.main',
                  borderRadius: 4,
                }}
              />
            </Box>
            <Chip label="Max %15" size="small" color="info" />
          </Box>
          <Typography variant="caption" color="text.secondary">
            Tedarikçi paylarını optimize etmek için önerilen değişim aralığı
          </Typography>
        </Paper>

        {/* Aksiyon Planı */}
        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
          📋 Adım Adım Aksiyon Planı
        </Typography>
        <List disablePadding>
          {actions.map((action, index) => (
            <ListItem
              key={action.id}
              divider={index < actions.length - 1}
              sx={{ py: 2 }}
            >
              <ListItemIcon>
                {action.icon}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2" fontWeight="medium">
                      {action.id}. {action.title}
                    </Typography>
                    <Chip
                      label={getStatusLabel(action.change)}
                      size="small"
                      color={getStatusColor(action.change)}
                    />
                  </Box>
                }
                secondary={
                  <Box display="flex" gap={2} mt={1}>
                    <Typography variant="caption" color="text.secondary">
                      Mevcut: {action.current.toFixed(0)} {action.unit}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      → Önerilen: {action.recommended.toFixed(0)} {action.unit}
                    </Typography>
                    <Typography
                      variant="caption"
                      color={action.change > 0 ? 'success.main' : 'error.main'}
                      fontWeight="bold"
                    >
                      {action.change > 0 ? '+' : ''}{action.change.toFixed(0)} {action.unit}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>

        {/* Öneri Diyaloğu */}
        {serviceLevel < 0.90 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Servis seviyesi hedefin altında (%95). Önerilen aksiyonları uygulayarak
            servis seviyesini artırabilirsiniz.
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          startIcon={<Download />}
          onClick={onExport}
        >
          Excel'e Aktar
        </Button>
        <Button
          variant="outlined"
          startIcon={<Schedule />}
          onClick={onSchedule}
        >
          1 Ay Sonra Kontrol Et
        </Button>
        <Button
          variant="contained"
          endIcon={<Close />}
          onClick={onClose}
          sx={{ ml: 'auto' }}
        >
          Kapat
        </Button>
      </DialogActions>
    </Dialog>
  );
}