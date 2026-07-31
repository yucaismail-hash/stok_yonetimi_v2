// frontend/src/pages/DashboardPage.tsx - TAM VE GÜNCEL (YENİ BİLEŞENLERLE)

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Stack,
  Skeleton,
  Tooltip,
  Stepper,
  Step,
  StepLabel,
  Drawer,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircle,
  CloudUpload,
  Close,
  Warning,
  ArrowForward,
  Lightbulb,
  Assessment,
  TrendingUp,
  TrendingDown,
  Remove,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import api, { buildDataset } from '../../services/api';
import { styled } from '@mui/material/styles';
import {
  Shield,
  TrendingUp as TrendingUpLucide,
  Dice5,
  School as SchoolLucide,
  Truck,
  Clock,
  Database,
  Bot,
} from 'lucide-react';
import {
  AlertItem,
  DashboardChangeResponse,
  ModuleChanges,
  ChangeItem,
  ActionDialogData,
  CriticalItem,
} from '../../types/dashboard';

// ✅ YENİ BİLEŞENLER
import ImportWizard from '../../components/ImportWizard';
import LearningScoreBadge from '../../components/Dashboard/LearningScoreBadge';
import AIContextPanel from '../../components/Dashboard/AIContextPanel';
import ExecutiveSummary from '../../components/Dashboard/ExecutiveSummary';
import TodaysDecision from '../../components/Dashboard/TodaysDecision';

// ============================================================
// 📌 INTERFACES
// ============================================================

interface Activity {
  id: number;
  type: string;
  message: string;
  time: string;
  status: 'success' | 'warning' | 'error' | 'info';
  details?: string;
  raw?: any;
}

interface AIExecutiveData {
  has_recommendation: boolean;
  summary: string;
  full_summary?: string;
  details?: string[];
  last_analysis_date?: string | null;
  confidence: number;
  action?: string;
  action_path?: string;
  action_label?: string;
  recommendations?: Array<{
    title: string;
    reason: string;
    action: string;
    path: string;
  }>;
  trend_summary?: any;
  risks?: any[];
  executive_recommendations?: string[];
}

interface DatasetStatus {
  id: number | null;
  file_name: string | null;
  product_count: number;
  period_count: number;
  data_points: number;
  created_at: string | null;
  is_active: boolean;
  status: 'ready' | 'old' | 'none';
  last_update: string | null;
}

interface HistoryItem {
  id: number;
  created_at: string;
  data: any;
  result_type: string;
  total_materials: number;
}

interface ModuleSummary {
  priority: number;
  summary: string;
  analysis_id: number | null;
  page: string;
  analysis_type: string;
  dataset_id: string | null;
  total_items?: number;
  critical_count?: number;
  high_risk_count?: number;
  avg_service_level?: number;
  trend_up?: number;
  trend_down?: number;
  created_at?: string;
}

interface DashboardSummary {
  modules: Record<string, ModuleSummary | null>;
  top_priority_module: string | null;
  top_priority: number;
  summary: string;
  updated_at: string;
}

interface Recommendation {
  analysis: string;
  priority: number;
  title: string;
  reason: string;
  expected_benefit: string;
  target_page: string;
  analysis_id: number | null;
  analysis_type: string;
  dataset_id: string | null;
}

interface AIRecommendationResponse {
  success: boolean;
  has_recommendation: boolean;
  message?: string;
  recommendation?: Recommendation & { priority_label?: string };
  ai_explanation?: string;
  target_page?: string;
  analysis_id?: number;
  analysis_type?: string;
  dataset_id?: string;
}

// ============================================================
// 📁 STYLED COMPONENTS
// ============================================================

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const UploadArea = styled(Paper)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.spacing(2),
  padding: theme.spacing(2),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s',
  backgroundColor: '#f8faff',
  minHeight: 80,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  '&:hover': {
    backgroundColor: '#f0f7ff',
    borderColor: '#1f4e79',
  },
  '&.dragging': {
    backgroundColor: '#e3f2fd',
    borderColor: '#1f4e79',
    transform: 'scale(1.02)',
  },
}));

// ============================================================
// 📌 YARDIMCI FONKSİYONLAR
// ============================================================

const getTimeAgo = (dateStr: string | null): string => {
  if (!dateStr) return 'Bugün';
  
  try {
    const parts = dateStr.split(' ');
    const datePart = parts[0];
    const timePart = parts[1]?.split('.')[0];
    
    if (!datePart || !timePart) return 'Bugün';
    
    const [year, month, day] = datePart.split('-').map(Number);
    const [hours, minutes, seconds] = timePart.split(':').map(Number);
    
    const utcDate = new Date(Date.UTC(year, month - 1, day, hours, minutes, seconds));
    const now = new Date();
    
    const diffMs = now.getTime() - utcDate.getTime();
    
    if (diffMs < 0) return 'Bugün';
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Şimdi';
    if (diffMins < 60) return `${diffMins} dakika önce`;
    if (diffHours < 24) return `${diffHours} saat önce`;
    if (diffDays < 7) return `${diffDays} gün önce`;
    
    return `${day}.${month}.${year}`;
  } catch (error) {
    return 'Bugün';
  }
};

const truncateFileName = (name: string, maxLength: number = 28): string => {
  if (!name) return 'Bilinmeyen';
  if (name.length <= maxLength) return name;
  const ext = name.split('.').pop() || '';
  const base = name.slice(0, maxLength - ext.length - 4);
  return `${base}...${ext}`;
};

const getPriorityColor = (priority: number): 'success' | 'warning' | 'error' | 'default' => {
  if (priority >= 90) return 'error';
  if (priority >= 70) return 'warning';
  if (priority >= 40) return 'default';
  return 'success';
};

const getPriorityLabel = (priority: number): string => {
  if (priority >= 90) return 'Kritik';
  if (priority >= 70) return 'Yüksek';
  if (priority >= 40) return 'Orta';
  return 'Düşük';
};

const getPriorityColorHex = (priority: number): string => {
  if (priority >= 90) return '#d32f2f';
  if (priority >= 70) return '#ed6c02';
  if (priority >= 40) return '#1976d2';
  return '#2e7d32';
};

const getChangeIcon = (change: number, improved: boolean) => {
  if (change === 0) return <Remove sx={{ fontSize: 14, color: '#9e9e9e' }} />;
  if (improved) return <TrendingDown sx={{ fontSize: 14, color: '#2e7d32' }} />;
  return <TrendingUp sx={{ fontSize: 14, color: '#d32f2f' }} />;
};

const getChangeColor = (change: number, improved: boolean) => {
  if (change === 0) return '#9e9e9e';
  if (improved) return '#2e7d32';
  return '#d32f2f';
};

const getChangePrefix = (change: number) => {
  if (change === 0) return '';
  if (change > 0) return '+';
  return '';
};

// ============================================================
// 📊 API FONKSİYONLARI (OPTİMİZE EDİLMİŞ)
// ============================================================

const fetchAllDashboardData = async () => {
  const [summary, aiRec, alerts, change] = await Promise.all([
    api.get('/api/dashboard/summary').catch(() => ({ data: { success: false, data: { modules: {} } } })),
    api.get('/api/dashboard/ai-recommendation').catch(() => ({ data: { success: true, has_recommendation: false } })),
    api.get('/api/dashboard/alerts').catch(() => ({ data: { success: true, alerts: [] } })),
    api.get('/api/dashboard/change').catch(() => ({ data: { success: true, changes: {}, gains: [], has_changes: false } })),
  ]);
  
  return {
    summary: summary.data,
    aiRecommendation: aiRec.data,
    alerts: alerts.data,
    change: change.data,
  };
};

// ============================================================
// 📊 BİLEŞENLER
// ============================================================

// ✅ Executive Summary Drawer
const ExecutiveDrawer = ({
  open,
  onClose,
  data,
}: {
  open: boolean;
  onClose: () => void;
  data: AIExecutiveData | null;
}) => {
  if (!data) return null;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width: { xs: '100%', sm: 480, md: 560 },
            p: 3,
            bgcolor: '#f8faff',
          },
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.1rem' }}>
          📊 Executive Summary
        </Typography>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </Box>

      <Divider sx={{ mb: 2 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 0.5, fontSize: '0.8rem' }}>
            Özet
          </Typography>
          <Typography variant="body2" sx={{ color: '#374151', lineHeight: 1.8, fontSize: '0.85rem' }}>
            {data.full_summary || data.summary}
          </Typography>
        </Box>

        {data.trend_summary && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 0.5, fontSize: '0.8rem' }}>
              📈 Trend Özeti
            </Typography>
            <Typography variant="body2" sx={{ color: '#374151', lineHeight: 1.8, fontSize: '0.85rem' }}>
              {data.trend_summary.summary || 'Trend bilgisi mevcut değil.'}
            </Typography>
            {data.trend_summary.trend_direction && (
              <Chip
                label={`Trend: ${data.trend_summary.trend_direction}`}
                size="small"
                color={data.trend_summary.trend_direction === 'İyileşiyor' ? 'success' : 
                       data.trend_summary.trend_direction === 'Kötüleşiyor' ? 'error' : 'default'}
                sx={{ mt: 1, height: 20, fontSize: '0.55rem' }}
              />
            )}
          </Box>
        )}

        {data.risks && data.risks.length > 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 0.5, fontSize: '0.8rem' }}>
              ⚠️ Riskler
            </Typography>
            <List disablePadding>
              {data.risks.slice(0, 5).map((risk, idx) => (
                <ListItem key={idx} sx={{ px: 0, py: 0.25 }}>
                  <ListItemIcon sx={{ minWidth: 28 }}>
                    <Warning color="warning" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={typeof risk === 'string' ? risk : risk.description || JSON.stringify(risk)}
                    sx={{ '& .MuiListItemText-primary': { fontSize: '0.8rem', color: '#374151' } }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {data.executive_recommendations && data.executive_recommendations.length > 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 0.5, fontSize: '0.8rem' }}>
              💡 Tavsiyeler
            </Typography>
            <List disablePadding>
              {data.executive_recommendations.map((rec, idx) => (
                <ListItem key={idx} sx={{ px: 0, py: 0.25 }}>
                  <ListItemIcon sx={{ minWidth: 28 }}>
                    <CheckCircle color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={rec}
                    sx={{ '& .MuiListItemText-primary': { fontSize: '0.8rem', color: '#374151' } }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box sx={{ mt: 1, p: 2, bgcolor: '#f0f7ff', borderRadius: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
            Son güncelleme: {data.last_analysis_date || 'Bugün'}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
            Güven seviyesi: %{Math.round((data.confidence || 0) * 100)}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
        <Button
          fullWidth
          variant="outlined"
          onClick={onClose}
          sx={{ borderRadius: 2, textTransform: 'none', fontSize: '0.75rem' }}
        >
          Kapat
        </Button>
      </Box>
    </Drawer>
  );
};

// ✅ AI Strategic Recommendation
const AIStrategicRecommendation = ({
  data,
  loading,
  onAction,
}: {
  data: AIRecommendationResponse | null;
  loading: boolean;
  onAction: (targetPage: string, analysisId: number | null, analysisType: string, datasetId: string | null) => void;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width="40%" height={20} />
          <Skeleton variant="text" width="80%" height={14} />
          <Skeleton variant="text" width="60%" height={14} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="rectangular" width={140} height={32} sx={{ borderRadius: 2 }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.has_recommendation || !data.recommendation) {
    return (
      <Card sx={{
        borderRadius: 3,
        border: '1px dashed #d0d0d0',
        bgcolor: '#fafafa',
      }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Avatar sx={{ bgcolor: '#e0e0e0', width: 40, height: 40 }}>
              <Lightbulb sx={{ fontSize: 18, color: '#9e9e9e' }} />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.7rem', letterSpacing: '0.5px' }}>
                🧠 AI Stratejik Öneri
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.8rem', mb: 0.5 }}>
                Analiz yaptığınız takdirde sonuçlar ile ilgili stratejik önerilerde bulunabilirim.
              </Typography>
              <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
                Henüz yeterli analiz verisi yok. Bir analiz çalıştırarak başlayın.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const rec = data.recommendation;
  const priorityColor = getPriorityColor(rec.priority);
  const priorityLabel = rec.priority_label || getPriorityLabel(rec.priority);
  const colorHex = getPriorityColorHex(rec.priority);

  const handleNavigate = () => {
    console.log('🔍 AI Öneri Navigasyon:', {
      targetPage: rec.target_page,
      analysisId: rec.analysis_id,
      analysisType: rec.analysis_type,
      datasetId: rec.dataset_id,
    });
    onAction(rec.target_page, rec.analysis_id, rec.analysis_type, rec.dataset_id);
  };

  return (
    <Card sx={{
      borderRadius: 3,
      border: `1px solid ${colorHex}30`,
      bgcolor: `${colorHex}08`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: colorHex }} />
      
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Avatar sx={{ bgcolor: `${colorHex}15`, color: colorHex, width: 40, height: 40 }}>
            <Lightbulb sx={{ fontSize: 18 }} />
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 700, color: colorHex, fontSize: '0.7rem', letterSpacing: '0.5px' }}>
                🧠 AI Stratejik Öneri
              </Typography>
              <Chip
                label={`${priorityLabel} · Öncelik ${rec.priority}`}
                size="small"
                color={priorityColor}
                sx={{ height: 20, fontSize: '0.5rem', fontWeight: 600 }}
              />
            </Box>
            
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.95rem', mb: 0.25 }}>
              {rec.title}
            </Typography>
            
            <Typography variant="body2" sx={{ color: '#374151', fontSize: '0.8rem', mb: 0.5, lineHeight: 1.5 }}>
              {rec.reason}
            </Typography>

            {rec.expected_benefit && (
              <Box sx={{ mb: 1, pl: 1 }}>
                <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem', fontWeight: 600, display: 'block', mb: 0.25 }}>
                  Beklenen Fayda
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#374151', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <CheckCircle sx={{ fontSize: 12, color: 'success.main' }} /> {rec.expected_benefit}
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
              <Button
                variant="contained"
                size="small"
                endIcon={<ArrowForward sx={{ fontSize: 16 }} />}
                onClick={handleNavigate}
                sx={{
                  bgcolor: colorHex,
                  '&:hover': { bgcolor: colorHex, opacity: 0.85 },
                  borderRadius: 2,
                  textTransform: 'none',
                  fontSize: '0.7rem',
                  px: 2.5,
                  py: 0.5,
                }}
              >
                📊 Analizi Aç
              </Button>
              {rec.analysis_type && (
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#9e9e9e' }}>
                  İlgili analiz: {rec.analysis_type}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

// ✅ Analysis Highlights
const AnalysisHighlights = ({
  modules,
  loading,
  onOpen,
}: {
  modules: Record<string, ModuleSummary | null> | undefined;
  loading: boolean;
  onOpen: (page: string, analysisId: number | null, analysisType: string, datasetId: string | null) => void;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={140} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Grid container spacing={1.5}>
              {[1, 2, 3, 4, 5].map((i) => (
                <Grid size={{ xs: 12, sm: 6, md: 2.4 }} key={i}>
                  <Skeleton variant="rectangular" height={72} sx={{ borderRadius: 2 }} />
                </Grid>
              ))}
            </Grid>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!modules) return null;

  const activeModules = Object.entries(modules)
    .filter(([_, data]) => data !== null)
    .map(([key, data]) => ({ key, ...data })) as Array<{ key: string } & ModuleSummary>;

  if (activeModules.length === 0) return null;

  const sorted = activeModules.sort((a, b) => b.priority - a.priority);
  const topFive = sorted.slice(0, 5);

  const moduleConfig: Record<string, { icon: React.ReactNode; color: string; label: string; getMetric?: (data: ModuleSummary) => string }> = {
    forecast: { 
      icon: <TrendingUpLucide width={16} height={16}/>, 
      color: '#1976d2', 
      label: 'Talep Tahmini',
      getMetric: (data) => data.trend_up ? `↑%${data.trend_up}` : ''
    },
    safety_stock: { 
      icon: <Shield width={16} height={16} />, 
      color: '#2e7d32', 
      label: 'Emniyet Stoğu',
      getMetric: (data) => data.critical_count ? `${data.critical_count} Kritik` : ''
    },
    supplier: { 
      icon: <Truck width={16} height={16} />, 
      color: '#d32f2f', 
      label: 'Tedarikçi',
      getMetric: (data) => data.high_risk_count ? `${data.high_risk_count} Riskli` : ''
    },
    simulation: { 
      icon: <Dice5 width={16} height={16} />, 
      color: '#9c27b0', 
      label: 'Simülasyon',
      getMetric: () => ''
    },
    backtest: { 
      icon: <SchoolLucide width={16} height={16} />, 
      color: '#ed6c02', 
      label: 'Backtest',
      getMetric: (data) => data.avg_service_level ? `%${Math.round(data.avg_service_level)}` : ''
    },
  };

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Assessment sx={{ fontSize: 18, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            📊 Analizlerden Öne Çıkan Bulgular
          </Typography>
          <Chip
            label={`${topFive.length} / ${activeModules.length}`}
            size="small"
            sx={{ height: 16, fontSize: '0.45rem', bgcolor: '#f0f7ff' }}
          />
        </Box>

        <Grid container spacing={1.5}>
          {topFive.map((module) => {
            const config = moduleConfig[module.key] || {
              icon: <Assessment sx={{ fontSize: 16 }} />,
              color: '#6b7280',
              label: module.key,
            };
            const priorityColor = getPriorityColor(module.priority);
            const colorHex = getPriorityColorHex(module.priority);
            const metric = config.getMetric ? config.getMetric(module) : '';

            return (
              <Grid size={{ xs: 12, sm: 6, md: 2.4 }} key={module.key}>
                <Paper
                  sx={{
                    p: 1.25,
                    border: `1px solid ${colorHex}20`,
                    borderRadius: 2,
                    bgcolor: `${colorHex}05`,
                    transition: 'all 0.2s',
                    cursor: 'pointer',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 2,
                      borderColor: colorHex,
                    },
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                  onClick={() => onOpen(module.page, module.analysis_id, module.analysis_type, module.dataset_id)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.25 }}>
                    <Avatar sx={{ bgcolor: `${config.color}15`, color: config.color, width: 22, height: 22 }}>
                      {config.icon}
                    </Avatar>
                    <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.55rem', color: '#374151' }}>
                      {config.label}
                    </Typography>
                  </Box>
                  
                  {metric && (
                    <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.75rem', color: config.color, mb: 0.25 }}>
                      {metric}
                    </Typography>
                  )}
                  
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.6rem', color: '#1f4e79', flex: 1, mb: 0.25 }}>
                    {module.summary}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 'auto' }}>
                    <Chip
                      label={getPriorityLabel(module.priority)}
                      size="small"
                      color={priorityColor}
                      sx={{ height: 16, fontSize: '0.45rem', fontWeight: 600, minWidth: 36 }}
                    />
                    <Typography variant="caption" sx={{ fontSize: '0.45rem', color: '#9e9e9e', display: 'flex', alignItems: 'center', gap: 0.25 }}>
                      Aç <ArrowForward sx={{ fontSize: 10 }} />
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
};

// ✅ Son Analizden Bu Yana Ne Değişti?
const ChangeSection = ({
  changes,
  loading,
}: {
  changes: DashboardChangeResponse | null;
  loading: boolean;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={200} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="rectangular" height={40} sx={{ mb: 1, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={40} sx={{ mb: 1, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={40} sx={{ borderRadius: 2 }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!changes || !changes.has_changes || Object.keys(changes.changes || {}).length === 0) {
    return (
      <Card sx={{
        borderRadius: 3,
        border: '1px dashed #d0d0d0',
        bgcolor: '#fafafa',
      }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Clock size={18} color="#9e9e9e" />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
                Son Analizden Bu Yana Ne Değişti?
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.75rem' }}>
                Henüz karşılaştırma yapılabilecek yeterli analiz verisi yok.
              </Typography>
              <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
                En az 2 analiz yapıldığında değişimler burada görünecektir.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const { changes: changeData } = changes;
  const moduleLabels: Record<string, string> = {
    forecast: 'Talep Tahmini',
    safety_stock: 'Emniyet Stoğu',
    supplier: 'Tedarikçi',
    simulation: 'Simülasyon',
    backtest: 'Backtest',
  };

  const changeItems: { module: string; label: string; data: ChangeItem; key: string }[] = [];

  Object.entries(changeData).forEach(([moduleKey, moduleChanges]) => {
    if (!moduleChanges) return;
    
    Object.entries(moduleChanges).forEach(([key, value]) => {
      if (key === '_meta') return;
      const item = value as ChangeItem;
      if (item && typeof item === 'object' && 'old' in item && 'new' in item && 'change' in item) {
        changeItems.push({
          module: moduleKey,
          label: item.label || key,
          data: item,
          key: `${moduleKey}_${key}`,
        });
      }
    });
  });

  if (changeItems.length === 0) {
    return (
      <Card sx={{
        borderRadius: 3,
        border: '1px dashed #d0d0d0',
        bgcolor: '#fafafa',
      }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Clock size={18} color="#9e9e9e" />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
                Son Analizden Bu Yana Ne Değişti?
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.75rem' }}>
                Henüz karşılaştırma yapılabilecek yeterli analiz verisi yok.
              </Typography>
              <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
                En az 2 analiz yapıldığında değişimler burada görünecektir.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Clock size={18} color="#1f4e79" />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            Son Analizden Bu Yana Ne Değişti?
          </Typography>
        </Box>

        <Stack spacing={1}>
          {changeItems.map((item) => {
            const change = item.data.change;
            const improved = item.data.improved;
            const color = getChangeColor(change, improved);
            const icon = getChangeIcon(change, improved);
            const prefix = getChangePrefix(change);
            const absChange = Math.abs(change);

            return (
              <Paper
                key={item.key}
                sx={{
                  p: 1.25,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  bgcolor: '#f8faff',
                  border: '1px solid #e8f0fe',
                  borderRadius: 2,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#374151', fontWeight: 500 }}>
                    {moduleLabels[item.module] || item.module}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e' }}>
                    {item.label}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e' }}>
                    {item.data.old}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#9e9e9e' }}>
                    →
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.75rem', color: color }}>
                    {item.data.new}
                  </Typography>
                  {change !== 0 && (
                    <Chip
                      icon={icon}
                      label={`${prefix}${absChange}`}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.5rem',
                        fontWeight: 600,
                        bgcolor: improved ? '#e8f5e9' : '#ffebee',
                        color: color,
                        border: `1px solid ${color}30`,
                        '& .MuiChip-icon': { fontSize: 12, margin: '0 2px' },
                      }}
                    />
                  )}
                </Box>
              </Paper>
            );
          })}
        </Stack>
      </CardContent>
    </Card>
  );
};

// ✅ İşletme Kazanımları
const GainsSection = ({
  gains,
  loading,
}: {
  gains: string[];
  loading: boolean;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={160} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="text" width="80%" height={14} />
            <Skeleton variant="text" width="70%" height={14} />
            <Skeleton variant="text" width="60%" height={14} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!gains || gains.length === 0) {
    return (
      <Card sx={{
        borderRadius: 3,
        border: '1px dashed #d0d0d0',
        bgcolor: '#fafafa',
      }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <CheckCircle sx={{ fontSize: 18, color: '#9e9e9e' }} />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
                İşletme Kazanımları
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.75rem' }}>
                Sistem sayesinde elde edilen kazanımlar burada listelenecektir.
              </Typography>
              <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
                Analizler yapıldıkça kazanımlar otomatik olarak hesaplanacaktır.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', bgcolor: '#f5f8fc' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <CheckCircle sx={{ fontSize: 18, color: '#2e7d32' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            İşletme Kazanımları
          </Typography>
          <Chip
            label={`${gains.length} gelişme`}
            size="small"
            color="success"
            sx={{ height: 18, fontSize: '0.5rem' }}
          />
        </Box>

        <Stack spacing={0.75}>
          {gains.slice(0, 5).map((gain, idx) => {
            const isWarning = gain.startsWith('⚠');
            return (
              <Box
                key={idx}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 0.75,
                  bgcolor: isWarning ? '#fff3e0' : '#e8f5e9',
                  borderRadius: 1.5,
                  border: `1px solid ${isWarning ? '#ffcc80' : '#a5d6a7'}`,
                }}
              >
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: isWarning ? '#e65100' : '#2e7d32' }}>
                  {gain}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      </CardContent>
    </Card>
  );
};

// ✅ Aksiyon Gerektiren Konular - Dialog
const ActionDialog = ({
  open,
  onClose,
  data,
  onNavigate,
}: {
  open: boolean;
  onClose: () => void;
  data: ActionDialogData | null;
  onNavigate: (targetPage: string, analysisId: number | null, analysisType: string, datasetId: string | null) => void;
}) => {
  if (!data) return null;

  const handleNavigate = () => {
    const datasetIdStr = data.dataset_id ? String(data.dataset_id) : null;
    onNavigate(
      data.target_page,
      data.analysis_id,
      data.analysis_type,
      datasetIdStr
    );
    onClose();
  };

  const getTableColumns = (items: CriticalItem[]) => {
    if (!items || items.length === 0) return [];
    
    const firstItem = items[0];
    const columns = ['code'];
    
    if (firstItem.current_stock !== undefined) columns.push('current_stock');
    if (firstItem.min_stock !== undefined) columns.push('min_stock');
    if (firstItem.estimated_days !== undefined) columns.push('estimated_days');
    if (firstItem.risk_score !== undefined) columns.push('risk_score');
    if (firstItem.ss !== undefined) columns.push('ss');
    
    return columns;
  };

  const columns = getTableColumns(data.critical_items);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 1.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.95rem' }}>
            ⚠️ {data.title}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <Close fontSize="small" />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ py: 2 }}>
        <Typography variant="body2" sx={{ color: '#374151', fontSize: '0.8rem', mb: 2 }}>
          {data.summary}
        </Typography>

        {data.critical_items && data.critical_items.length > 0 && (
          <>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem', mb: 1 }}>
              📋 Kritik Kayıtlar ({data.critical_items.length})
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1.5, mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f0f7ff' }}>
                    <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Kod</TableCell>
                    {columns.includes('current_stock') && (
                      <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Mevcut Stok</TableCell>
                    )}
                    {columns.includes('min_stock') && (
                      <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Minimum</TableCell>
                    )}
                    {columns.includes('estimated_days') && (
                      <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Tahmini Tükenme</TableCell>
                    )}
                    {columns.includes('risk_score') && (
                      <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Risk Skoru</TableCell>
                    )}
                    {columns.includes('ss') && (
                      <TableCell sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79' }}>Önerilen SS</TableCell>
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.critical_items.slice(0, 10).map((item, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell sx={{ fontSize: '0.65rem', fontWeight: 500 }}>{item.code}</TableCell>
                      {columns.includes('current_stock') && (
                        <TableCell sx={{ fontSize: '0.65rem' }}>{item.current_stock ?? '-'}</TableCell>
                      )}
                      {columns.includes('min_stock') && (
                        <TableCell sx={{ fontSize: '0.65rem' }}>{item.min_stock ?? '-'}</TableCell>
                      )}
                      {columns.includes('estimated_days') && (
                        <TableCell sx={{ fontSize: '0.65rem' }}>{item.estimated_days ?? '-'}</TableCell>
                      )}
                      {columns.includes('risk_score') && (
                        <TableCell sx={{ fontSize: '0.65rem' }}>{item.risk_score ?? '-'}</TableCell>
                      )}
                      {columns.includes('ss') && (
                        <TableCell sx={{ fontSize: '0.65rem' }}>{item.ss ?? '-'}</TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {data.critical_items.length > 10 && (
                <Box sx={{ p: 1, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                    +{data.critical_items.length - 10} daha kritik kayıt
                  </Typography>
                </Box>
              )}
            </TableContainer>
          </>
        )}

        {data.ai_comment && (
          <Box sx={{ p: 1.5, bgcolor: '#f3e5f5', borderRadius: 2, border: '1px solid #ce93d8', mb: 2 }}>
            <Typography variant="caption" sx={{ fontWeight: 600, color: '#6a1b9a', fontSize: '0.65rem', display: 'block', mb: 0.5 }}>
              🤖 AI Tavsiyesi
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4a148c' }}>
              {data.ai_comment}
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 1.5, px: 3 }}>
        <Button
          variant="contained"
          startIcon={<Assessment sx={{ fontSize: 18 }} />}
          onClick={handleNavigate}
          sx={{
            bgcolor: '#1f4e79',
            '&:hover': { bgcolor: '#1a3d5c' },
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '0.75rem',
            px: 3,
          }}
        >
          📊 {data.analysis_type} Analizini Aç
        </Button>
        <Button
          variant="outlined"
          onClick={onClose}
          sx={{ borderRadius: 2, textTransform: 'none', fontSize: '0.7rem' }}
        >
          Kapat
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// ✅ Quick Analysis Grid
const QuickAnalysisGrid = ({ onNavigate, loading }: { onNavigate: (path: string) => void; loading: boolean }) => {
  const analyses = [
    { key: 'forecast', title: 'Talep Tahmini', icon: <TrendingUpLucide width={18} height={18} />, color: '#1976d2', path: '/forecast' },
    { key: 'safety-stock', title: 'Emniyet Stoğu', icon: <Shield width={18} height={18} />, color: '#2e7d32', path: '/safety-stock' },
    { key: 'supplier', title: 'Tedarikçi', icon: <Truck width={18} height={18} />, color: '#d32f2f', path: '/supplier' },
    { key: 'simulation', title: 'Simülasyon', icon: <Dice5 width={18} height={18} />, color: '#9c27b0', path: '/simulation' },
    { key: 'backtest', title: 'Backtest', icon: <SchoolLucide width={18} height={18} />, color: '#ed6c02', path: '/backtest' },
  ];

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', height: '100%' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem', mb: 1.5 }}>
          ⚡ Hızlı Analiz
        </Typography>
        <Grid container spacing={1.5}>
          {analyses.map((analysis) => (
            <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={analysis.key}>
              <Paper
                sx={{
                  p: 1.25,
                  textAlign: 'center',
                  cursor: loading ? 'default' : 'pointer',
                  border: '1px solid #e8f0fe',
                  borderRadius: 2,
                  transition: 'all 0.2s',
                  '&:hover': loading ? {} : {
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                    borderColor: analysis.color,
                  },
                  opacity: loading ? 0.7 : 1,
                }}
                onClick={loading ? undefined : () => onNavigate(analysis.path)}
              >
                <Avatar sx={{ bgcolor: `${analysis.color}15`, color: analysis.color, width: 32, height: 32, mx: 'auto', mb: 0.5 }}>
                  {analysis.icon}
                </Avatar>
                <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.55rem', color: '#374151', display: 'block' }}>
                  {analysis.title}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

// ✅ Recent Analyses List
const RecentAnalysesList = ({
  historyItems,
  loading,
  onOpenAnalysis,
}: {
  historyItems: HistoryItem[];
  loading: boolean;
  onOpenAnalysis: (item: HistoryItem) => void;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', height: '100%' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={100} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="rectangular" height={36} sx={{ mb: 0.5, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={36} sx={{ mb: 0.5, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={36} sx={{ borderRadius: 2 }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  const recent = historyItems.slice(0, 5);

  const getTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      'forecast_batch': 'Talep Tahmini',
      'forecast_batch_async': 'Talep Tahmini',
      'safety_stock_batch': 'Emniyet Stoğu',
      'safety_stock_batch_async': 'Emniyet Stoğu',
      'simulation_batch': 'Simülasyon',
      'simulation_batch_async': 'Simülasyon',
      'backtest_batch': 'Backtest',
      'backtest_batch_async': 'Backtest',
      'supplier_batch': 'Tedarikçi Analizi',
      'supplier_batch_async': 'Tedarikçi Analizi',
    };
    return map[type] || type;
  };

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', height: '100%' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem', mb: 1.5 }}>
          📑 Son Analizler
        </Typography>
        
        {recent.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.7rem' }}>
              Henüz analiz yapılmadı
            </Typography>
            <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.6rem' }}>
              Forecast veya diğer analizleri çalıştırarak başlayın
            </Typography>
          </Box>
        ) : (
          <List disablePadding>
            {recent.map((item) => (
              <ListItem
                key={item.id}
                sx={{
                  px: 1,
                  py: 0.5,
                  borderBottom: '1px solid #f5f5f5',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemIcon sx={{ minWidth: 28 }}>
                  <CheckCircle sx={{ color: 'success.main', fontSize: 14 }} />
                </ListItemIcon>
                <ListItemText
                  primary={getTypeLabel(item.result_type)}
                  secondary={getTimeAgo(item.created_at)}
                  slotProps={{
                    primary: { variant: 'body2', sx: { fontWeight: 500, fontSize: '0.7rem' } },
                    secondary: { variant: 'caption', sx: { fontSize: '0.6rem', color: '#9e9e9e' } },
                  }}
                />
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => onOpenAnalysis(item)}
                  sx={{
                    fontSize: '0.5rem',
                    py: 0.25,
                    textTransform: 'none',
                    borderRadius: 1.5,
                    borderColor: '#d0d0d0',
                    color: '#374151',
                    '&:hover': { borderColor: '#1f4e79', color: '#1f4e79' },
                  }}
                >
                  Aç →
                </Button>
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

// ✅ Dataset Status Card
const DatasetStatusCard = ({ dataset, loading, onUpload }: { dataset: DatasetStatus; loading: boolean; onUpload: () => void }) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={120} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="text" width="80%" height={14} />
            <Skeleton variant="text" width="60%" height={14} />
            <Skeleton variant="text" width="40%" height={14} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'ready': return 'success';
      case 'old': return 'warning';
      case 'none': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'ready': return 'Hazır';
      case 'old': return 'Güncel Değil';
      case 'none': return 'Veri Yok';
      default: return 'Bilinmiyor';
    }
  };

  const displayName = truncateFileName(dataset.file_name || 'Bilinmeyen', 20);
  const timeAgo = getTimeAgo(dataset.created_at);

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Database size={16} color="#1f4e79" />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
            📂 Aktif Dataset
          </Typography>
          <Button
            size="small"
            variant="outlined"
            startIcon={<CloudUpload sx={{ fontSize: 14 }} />}
            onClick={onUpload}
            sx={{
              ml: 'auto',
              fontSize: '0.55rem',
              textTransform: 'none',
              borderRadius: 2,
              borderColor: '#1f4e79',
              color: '#1f4e79',
              '&:hover': { bgcolor: '#f0f7ff' },
              flexShrink: 0,
              py: 0.25,
              px: 1.5,
            }}
          >
            +Yeni
          </Button>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.55rem' }}>Dosya</Typography>
            <Tooltip title={dataset.file_name || 'Bilinmeyen'} arrow>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.7rem' }}>
                {displayName}
              </Typography>
            </Tooltip>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.55rem' }}>Ürün</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, color: '#374151', fontSize: '0.7rem' }}>
              {dataset.product_count.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.55rem' }}>Güncelleme</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, color: '#374151', fontSize: '0.7rem' }}>
              {timeAgo}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.55rem' }}>Durum</Typography>
            <Chip
              label={getStatusLabel(dataset.status)}
              size="small"
              color={getStatusColor(dataset.status)}
              sx={{
                height: 20,
                fontSize: '0.5rem',
                fontWeight: 600,
              }}
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

// ✅ ⚠️ Aksiyon Gerektiren Konular
const AttentionRequired = ({ 
  items, 
  loading, 
  onItemClick 
}: { 
  items: AlertItem[]; 
  loading: boolean; 
  onItemClick: (item: AlertItem) => void;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', bgcolor: '#faf9f7' }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Skeleton variant="text" width={200} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="rectangular" height={44} sx={{ mb: 1, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={44} sx={{ mb: 1, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={44} sx={{ borderRadius: 2 }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!items || items.length === 0) {
    return (
      <Card sx={{
        borderRadius: 3,
        border: '1px dashed #d0d0d0',
        bgcolor: '#fafafa',
      }}>
        <CardContent sx={{ py: 1.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Warning sx={{ fontSize: 18, color: '#9e9e9e' }} />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.8rem' }}>
                ⚠️ Aksiyon Gerektiren Konular
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.75rem' }}>
                Şu anda acil müdahale gerektiren bir durum bulunmuyor.
              </Typography>
              <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
                Sistem sağlıklı çalışıyor. Analizler devam ettikçe bu alan güncellenecektir.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const getSeverityColors = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { bg: '#fee8e8', border: '#f5c6c6', dot: '#d32f2f', text: '#5f2e2e', btnColor: '#d32f2f' };
      case 'warning':
        return { bg: '#fff3e0', border: '#ffcc80', dot: '#ed6c02', text: '#4e2e0e', btnColor: '#ed6c02' };
      case 'info':
        return { bg: '#fff8e1', border: '#ffd54f', dot: '#fbc02d', text: '#4e3d0e', btnColor: '#f57c00' };
      default:
        return { bg: '#f5f5f5', border: '#e0e0e0', dot: '#9e9e9e', text: '#374151', btnColor: '#6b7280' };
    }
  };

  return (
    <Card sx={{ 
      borderRadius: 3, 
      border: '1px solid #e8f0fe',
      bgcolor: '#faf9f7',
    }}>
      <CardContent sx={{ py: 1.5, px: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem', mb: 1.5 }}>
          ⚠️ Aksiyon Gerektiren Konular
        </Typography>
        
        <Stack spacing={1}>
          {items.slice(0, 5).map((item) => {
            const colors = getSeverityColors(item.severity);
            return (
              <Paper 
                key={item.id}
                sx={{ 
                  p: 1.25, 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  bgcolor: colors.bg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 2,
                  cursor: 'pointer',
                  '&:hover': { opacity: 0.85 },
                }}
                onClick={() => onItemClick(item)}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: colors.dot, flexShrink: 0 }} />
                  <Box>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', color: colors.text, fontWeight: 500 }}>
                      {item.title}
                    </Typography>
                    <Typography variant="caption" sx={{ fontSize: '0.65rem', color: colors.text, opacity: 0.8 }}>
                      {item.description}
                    </Typography>
                  </Box>
                </Box>
                <Button 
                  size="small" 
                  variant="text" 
                  sx={{ fontSize: '0.65rem', textTransform: 'none', color: colors.btnColor, minWidth: 'auto', ml: 1 }}
                >
                  {item.action_label} →
                </Button>
              </Paper>
            );
          })}
        </Stack>
      </CardContent>
    </Card>
  );
};

// ============================================================
// 📌 ANA DASHBOARD COMPONENT
// ============================================================

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 📌 AI ve Sistem State'leri
  const [aiExecutive, setAiExecutive] = useState<AIExecutiveData | null>(null);
  const [aiLoading, setAiLoading] = useState(true);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [hasDataset, setHasDataset] = useState(false);
  const [attentionItems, setAttentionItems] = useState<AlertItem[]>([]);
  const [attentionLoading, setAttentionLoading] = useState(true);

  // 📌 Change ve Gains State'leri
  const [changeData, setChangeData] = useState<DashboardChangeResponse | null>(null);
  const [changeLoading, setChangeLoading] = useState(true);
  const [gains, setGains] = useState<string[]>([]);

  // 📌 Action Dialog State
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionDialogData, setActionDialogData] = useState<ActionDialogData | null>(null);

  // 📌 Dataset State
  const [datasetStatus, setDatasetStatus] = useState<DatasetStatus>({
    id: null,
    file_name: null,
    product_count: 0,
    period_count: 0,
    data_points: 0,
    created_at: null,
    is_active: false,
    status: 'none',
    last_update: null,
  });
  const [datasetLoading, setDatasetLoading] = useState(true);

  // 📌 UI State'leri
  const [executiveDrawerOpen, setExecutiveDrawerOpen] = useState(false);
  
  // ✅ YENİ - Import Wizard State
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardFile, setWizardFile] = useState<File | null>(null);

  // 📌 Ref'ler
  const dataLoadedRef = useRef(false);
  const initialLoadDoneRef = useRef(false);

  // ============================================================
  // 📌 useQuery - Tek bir query'de tüm dashboard verileri
  // ============================================================
  const { data: dashboardData, isLoading: dashboardLoading, refetch: refetchDashboard } = useQuery({
    queryKey: ['dashboard-all', user?.id],
    queryFn: fetchAllDashboardData,
    enabled: !!user,
    staleTime: 120000,
    gcTime: 300000,
    retry: 1,
  });

  // ============================================================
  // 📌 hasData HESAPLA (useMemo ile optimize)
  // ============================================================
  const hasData = useMemo(() => {
    return hasDataset || datasetStatus.status !== 'none' || allActivities.length > 0 || historyItems.length > 0;
  }, [hasDataset, datasetStatus.status, allActivities.length, historyItems.length]);

  // ============================================================
  // 📌 CALLBACK'LER
  // ============================================================

  const fetchDatasetStatus = useCallback(async () => {
    if (dataLoadedRef.current && hasDataset) {
      return;
    }
    
    setDatasetLoading(true);
    try {
      const [uploadRes, resultsRes, datasetsRes] = await Promise.all([
        api.get('/api/upload/status'),
        api.get('/api/upload/results', { params: { limit: 1 } }),
        api.get('/api/upload/datasets?limit=1'),
      ]);
      
      const hasUploadedData = uploadRes.data.has_data === true;
      const hasAnalysisResults = resultsRes.data.success && resultsRes.data.results?.length > 0;
      const hasAnyData = hasUploadedData || hasAnalysisResults;
      
      if (!hasAnyData) {
        setDatasetStatus({
          id: null,
          file_name: null,
          product_count: 0,
          period_count: 0,
          data_points: 0,
          created_at: null,
          is_active: false,
          status: 'none',
          last_update: null,
        });
        setHasDataset(false);
        setDatasetLoading(false);
        return;
      }
      
      const ds = datasetsRes.data.datasets?.[0];
      if (ds && ds.is_active) {
        const createdDate = new Date(ds.created_at);
        const now = new Date();
        const diffHours = (now.getTime() - createdDate.getTime()) / (1000 * 60 * 60);

        setDatasetStatus({
          id: ds.id,
          file_name: ds.source_name || 'Bilinmeyen',
          product_count: ds.product_count || 0,
          period_count: ds.period_count || 0,
          data_points: ds.data_points || 0,
          created_at: ds.created_at,
          is_active: ds.is_active,
          status: ds.is_active ? (diffHours > 24 ? 'old' : 'ready') : 'none',
          last_update: ds.created_at,
        });
        setHasDataset(true);
      } else {
        setDatasetStatus({
          id: null,
          file_name: null,
          product_count: 0,
          period_count: 0,
          data_points: 0,
          created_at: null,
          is_active: false,
          status: 'none',
          last_update: null,
        });
        setHasDataset(hasAnalysisResults);
      }
    } catch (error) {
      console.error('❌ Dataset durumu alınamadı:', error);
      setDatasetStatus({
        id: null,
        file_name: null,
        product_count: 0,
        period_count: 0,
        data_points: 0,
        created_at: null,
        is_active: false,
        status: 'none',
        last_update: null,
      });
      setHasDataset(false);
    } finally {
      setDatasetLoading(false);
    }
  }, [hasDataset]);

  const fetchAIExecutiveSummary = useCallback(async () => {
    if (aiExecutive && aiExecutive.has_recommendation) {
      return;
    }
    
    setAiLoading(true);
    try {
      const token = localStorage.getItem('access_token') || 
                    JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.token;

      const res = await api.get('/api/dashboard/ai-summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.data.executive_summary) {
        const executive = res.data.executive_summary;
        const userData = res.data;
        
        const summaryText = executive.summary || 'Analizleriniz başarıyla tamamlandı.';
        const recommendations = executive.recommendations || [];
        const risks = executive.risks || [];
        const confidence = executive.confidence || 0.85;
        
        let action = 'Detaylı Raporları Gör';
        let action_path = '/tasks';
        let action_label = 'Raporları Gör';
        
        if (executive.top_action) {
          action = executive.top_action.title || action;
          action_path = executive.top_action.path || action_path;
          action_label = executive.top_action.label || action_label;
        }
        
        const formattedRecommendations = [];
        
        if (recommendations && recommendations.length > 0) {
          recommendations.forEach((rec: string) => {
            let title = 'Analiz';
            let path = '/tasks';
            const recLower = rec.toLowerCase();
            
            if (recLower.includes('tahmin') || recLower.includes('forecast')) {
              title = 'Talep Tahmini';
              path = '/forecast';
            } else if (recLower.includes('stok') || recLower.includes('safety')) {
              title = 'Emniyet Stoğu';
              path = '/safety-stock';
            } else if (recLower.includes('simülasyon') || recLower.includes('simulation')) {
              title = 'Simülasyon';
              path = '/simulation';
            } else if (recLower.includes('backtest')) {
              title = 'Backtest';
              path = '/backtest';
            } else if (recLower.includes('tedarikçi') || recLower.includes('supplier')) {
              title = 'Tedarikçi Analizi';
              path = '/supplier';
            }
            
            formattedRecommendations.push({
              title: title,
              reason: rec.length > 100 ? rec.substring(0, 100) + '...' : rec,
              action: 'Başlat',
              path: path,
            });
          });
        } else {
          formattedRecommendations.push({
            title: 'Talep Tahmini',
            reason: 'Güncel talep verileri ile stok planlaması optimize edilebilir.',
            action: 'Başlat',
            path: '/forecast',
          });
          formattedRecommendations.push({
            title: 'Emniyet Stoğu',
            reason: 'Kritik ürünler için güncel analiz önerilir.',
            action: 'Başlat',
            path: '/safety-stock',
          });
        }

        setAiExecutive({
          has_recommendation: true,
          summary: summaryText,
          full_summary: summaryText + (recommendations.length > 0 ? '\n\n' + recommendations.join('\n') : ''),
          details: executive.key_insights || executive.critical_attention || [],
          last_analysis_date: userData.executive_updated_at ? new Date(userData.executive_updated_at).toLocaleDateString('tr-TR') : 'Bugün',
          confidence: confidence,
          action: action,
          action_path: action_path,
          action_label: action_label,
          recommendations: formattedRecommendations.slice(0, 3),
          trend_summary: userData.trend_summary || null,
          risks: risks,
          executive_recommendations: recommendations,
        });
      } else {
        setAiExecutive({
          has_recommendation: false,
          summary: '',
          full_summary: '',
          confidence: 0,
          recommendations: [],
        });
      }
    } catch (error) {
      console.error('❌ AI özet hatası:', error);
      setAiExecutive({
        has_recommendation: false,
        summary: '',
        full_summary: '',
        confidence: 0,
        recommendations: [],
      });
    } finally {
      setAiLoading(false);
    }
  }, [aiExecutive]);

  // ✅ Dashboard verilerini useQuery'den al
  useEffect(() => {
    if (dashboardData) {
      // Alerts
      if (dashboardData.alerts?.alerts) {
        const items: AlertItem[] = dashboardData.alerts.alerts.map((alert: any) => ({
          id: alert.id || `alert_${Date.now()}`,
          severity: alert.severity || 'info',
          title: alert.title || 'Uyarı',
          description: alert.description || '',
          action_label: alert.action_label || 'İncele',
          action_path: alert.action_path || '/dashboard',
          priority: alert.priority || 0,
          analysis_id: alert.analysis_id || 0,
          analysis_type: alert.analysis_type || 'Analiz',
          dataset_id: alert.dataset_id || null,
          critical_items: alert.critical_items || [],
          ai_comment: alert.ai_comment || '',
        }));
        setAttentionItems(items);
        setAttentionLoading(false);
      }
      
      // Change
      if (dashboardData.change) {
        setChangeData(dashboardData.change);
        setGains(dashboardData.change.gains || []);
        setChangeLoading(false);
      }
    }
  }, [dashboardData]);

  const fetchHistory = useCallback(async () => {
    if (dataLoadedRef.current) return;
    
    setHistoryLoading(true);
    try {
      const res = await api.get('/api/upload/results', { params: { limit: 20 } });
      if (res.data.success) {
        const items = res.data.results || [];
        setHistoryItems(items);
      }
    } catch (error) {
      console.error('❌ Geçmiş hatası:', error);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const fetchActivities = useCallback(async () => {
    if (dataLoadedRef.current && allActivities.length > 0) return;
    
    try {
      const res = await api.get('/api/upload/results', { params: { limit: 100 } });
      const results = res.data.results || [];
      const activityList: Activity[] = results.map((item: any, index: number) => {
        const typeMap: Record<string, string> = {
          'forecast_batch': 'Talep Tahmini',
          'forecast_batch_async': 'Talep Tahmini',
          'safety_stock_batch': 'Emniyet Stoğu',
          'safety_stock_batch_async': 'Emniyet Stoğu',
          'simulation_batch': 'Monte Carlo Simülasyonu',
          'simulation_batch_async': 'Monte Carlo Simülasyonu',
          'backtest_batch': 'Backtest',
          'backtest_batch_async': 'Backtest',
          'supplier_batch': 'Tedarikçi Analizi',
          'supplier_batch_async': 'Tedarikçi Analizi',
        };
        const type = typeMap[item.result_type] || item.result_type || 'Analiz';
        let totalMaterials = item.total_materials || item.total || 0;
        const message = `${type}${totalMaterials > 0 ? ` - ${totalMaterials} malzeme` : ''}`;
        return {
          id: index,
          type: item.result_type || 'analysis',
          message: message,
          time: new Date(item.created_at).toLocaleString('tr-TR'),
          status: 'success' as const,
          details: item.result_type || 'Analiz',
          raw: item,
        };
      });
      activityList.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
      setAllActivities(activityList);
      setActivities(activityList.slice(0, 8));
    } catch (error) {
      console.error('❌ Aktivite hatası:', error);
    }
  }, [allActivities.length]);

  const loadAllData = useCallback(async () => {
    if (dataLoadedRef.current) return;
    
    setLoading(true);
    try {
      await Promise.all([
        fetchDatasetStatus(),
        fetchAIExecutiveSummary(),
        fetchActivities(),
        fetchHistory(),
      ]);
      dataLoadedRef.current = true;
    } catch (error) {
      console.error('❌ Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchDatasetStatus, fetchAIExecutiveSummary, fetchActivities, fetchHistory]);

  // ============================================================
  // 📌 useEffect
  // ============================================================
  useEffect(() => {
    if (user && !initialLoadDoneRef.current) {
      initialLoadDoneRef.current = true;
      loadAllData();
    }
  }, [user, loadAllData]);

  useEffect(() => {
    if (uploadSuccess) {
      fetchDatasetStatus();
      fetchAIExecutiveSummary();
      refetchDashboard();
      setTimeout(() => setUploadSuccess(false), 3000);
    }
  }, [uploadSuccess, fetchDatasetStatus, fetchAIExecutiveSummary, refetchDashboard]);

  // ============================================================
  // 📌 NAVIGATION HANDLERS
  // ============================================================

  const handleNavigateWithContext = (
    targetPage: string,
    analysisId: number | null,
    analysisType: string,
    datasetId: string | null
  ) => {
    console.log('🔍 Navigasyon:', { targetPage, analysisId, analysisType, datasetId });
    
    if (!targetPage || targetPage === '/dashboard' || targetPage === '') {
      console.warn('⚠️ Geçersiz targetPage, analiz türüne göre yönlendiriliyor');
      const defaultPages: Record<string, string> = {
        'forecast': '/forecast',
        'safety_stock': '/safety-stock',
        'supplier': '/supplier',
        'simulation': '/simulation',
        'backtest': '/backtest',
      };
      targetPage = defaultPages[analysisType] || '/dashboard';
    }
    
    if (analysisId) {
      sessionStorage.setItem('loadAnalysisId', String(analysisId));
      sessionStorage.setItem('loadAnalysisType', analysisType);
      if (datasetId) {
        sessionStorage.setItem('loadDatasetId', String(datasetId));
      }
    } else {
      console.warn('⚠️ analysis_id yok, sadece sayfaya yönlendiriliyor');
    }
    
    window.location.href = targetPage;
  };

  const handleOpenHistory = (item: HistoryItem) => {
    sessionStorage.setItem('loadAnalysisId', String(item.id));
    sessionStorage.setItem('loadAnalysisType', item.result_type);
    
    const typeMap: Record<string, string> = {
      'forecast_batch': '/forecast',
      'forecast_batch_async': '/forecast',
      'safety_stock_batch': '/safety-stock',
      'safety_stock_batch_async': '/safety-stock',
      'simulation_batch': '/simulation',
      'simulation_batch_async': '/simulation',
      'backtest_batch': '/backtest',
      'backtest_batch_async': '/backtest',
      'supplier_batch': '/supplier',
      'supplier_batch_async': '/supplier',
    };
    
    const path = typeMap[item.result_type] || '/dashboard';
    window.location.href = path;
  };

  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  // ============================================================
  // 📌 ACTION DIALOG HANDLERS
  // ============================================================
  const handleActionItemClick = (item: AlertItem) => {
    const dialogData: ActionDialogData = {
      title: item.title,
      summary: item.description,
      critical_items: item.critical_items || [],
      ai_comment: item.ai_comment || 'Analiz sonuçları için ilgili sayfayı ziyaret edin.',
      analysis_id: item.analysis_id || 0,
      analysis_type: item.analysis_type || 'Analiz',
      target_page: item.action_path || '/dashboard',
      dataset_id: item.dataset_id || null,
    };
    
    setActionDialogData(dialogData);
    setActionDialogOpen(true);
  };

  const handleActionDialogNavigate = (
    targetPage: string,
    analysisId: number | null,
    analysisType: string,
    datasetId: string | null
  ) => {
    if (analysisId) {
      sessionStorage.setItem('loadAnalysisId', String(analysisId));
      sessionStorage.setItem('loadAnalysisType', analysisType);
      if (datasetId) {
        sessionStorage.setItem('loadDatasetId', datasetId);
      }
    }
    window.location.href = targetPage;
  };

  // ============================================================
  // 📌 IMPORT WIZARD HANDLERS
  // ============================================================
  const handleOpenWizard = (file?: File) => {
    if (file) {
      setWizardFile(file);
    } else {
      setWizardFile(null);
    }
    setWizardOpen(true);
  };

  const handleWizardComplete = (datasetId: number) => {
    setWizardOpen(false);
    setWizardFile(null);
    setSuccessMessage('✅ Dataset başarıyla oluşturuldu!');
    fetchDatasetStatus();
    fetchAIExecutiveSummary();
    refetchDashboard();
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      handleOpenWizard(file);
      event.target.value = '';
    }
  };

  // ============================================================
  // 📌 RENDER
  // ============================================================
  const userName = user?.full_name || user?.email?.split('@')[0] || 'Kullanıcı';

  // Dashboard verilerini useQuery'den al
  const dashboardSummaryData = dashboardData?.summary;
  const aiRecommendationData = dashboardData?.aiRecommendation;
  const summaryLoading = dashboardLoading;
  const aiRecLoading = dashboardLoading;

  return (
    <Box sx={{ 
      bgcolor: '#f5f8fc', 
      minHeight: '100vh',
      p: { xs: 2, sm: 3 },
      mx: -3,
      mt: -3,
    }}>
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* ✅ YENİ IMPORT WIZARD */}
      <ImportWizard
        open={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          setWizardFile(null);
        }}
        onComplete={handleWizardComplete}
      />

      {/* Executive Summary Drawer */}
      <ExecutiveDrawer
        open={executiveDrawerOpen}
        onClose={() => setExecutiveDrawerOpen(false)}
        data={aiExecutive}
      />

      {/* Action Dialog */}
      <ActionDialog
        open={actionDialogOpen}
        onClose={() => setActionDialogOpen(false)}
        data={actionDialogData}
        onNavigate={handleActionDialogNavigate}
      />

      {/* ANA GRID */}
      <Grid container spacing={3}>
        {/* SOL SÜTUN - %70 */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Stack spacing={2.5}>
            {/* 1. Learning Score Badge - ÜSTTE */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <LearningScoreBadge variant="compact" />
            </Box>

            {/* 2. Executive Summary */}
            <ExecutiveSummary
              data={aiExecutive ? {
                summary: aiExecutive.summary || 'Analiz sonuçlarınız burada görünecek.',
                details: {
                  total_products: 0,
                  critical_products: 0,
                  avg_risk_score: 0,
                  avg_service_level: 0,
                  riskiest_group: '-',
                  top_problem: aiExecutive.details?.[0] || 'Henüz problem tespit edilmedi.',
                  top_recommendation: aiExecutive.executive_recommendations?.[0] || 'Henüz öneri yok.',
                },
                confidence: aiExecutive.confidence || 0,
                last_analysis_date: aiExecutive.last_analysis_date || 'Bugün',
              } : null}
              loading={aiLoading}
              onReadMore={() => setExecutiveDrawerOpen(true)}
            />

            {/* 3. Bugünün Kararı */}
            <TodaysDecision />

            {/* 4. AI Strategic Recommendation */}
            {aiRecommendationData && aiRecommendationData.has_recommendation && (
              <AIStrategicRecommendation
                data={aiRecommendationData}
                loading={aiRecLoading}
                onAction={handleNavigateWithContext}
              />
            )}

            {/* 5. Analysis Highlights */}
            <AnalysisHighlights
              modules={dashboardSummaryData?.data?.modules}
              loading={summaryLoading}
              onOpen={handleNavigateWithContext}
            />

            {/* 6. AI İşletmenizi Tanıyor */}
            <AIContextPanel maxItems={6} />

            {/* 7. Son Analizden Bu Yana Ne Değişti? */}
            <ChangeSection changes={changeData} loading={changeLoading} />

            {/* 8. İşletme Kazanımları */}
            <GainsSection gains={gains} loading={changeLoading} />

            {/* 9. Aksiyon Gerektiren Konular */}
            <AttentionRequired 
              items={attentionItems} 
              loading={attentionLoading} 
              onItemClick={handleActionItemClick}
            />

            {/* 10. Quick Analysis */}
            <QuickAnalysisGrid onNavigate={navigateTo} loading={loading} />
          </Stack>
        </Grid>

        {/* SAĞ SÜTUN - %30 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={2.5}>
            {/* Learning Score Detaylı */}
            <LearningScoreBadge variant="full" showDetails />

            {/* Active Dataset */}
            <DatasetStatusCard
              dataset={datasetStatus}
              loading={datasetLoading}
              onUpload={() => handleOpenWizard()}
            />

            {/* Recent Analyses */}
            <RecentAnalysesList
              historyItems={historyItems}
              loading={historyLoading}
              onOpenAnalysis={handleOpenHistory}
            />
          </Stack>
        </Grid>
      </Grid>

      {/* Gizli file input */}
      <VisuallyHiddenInput
        id="file-upload-input"
        type="file"
        accept=".xlsx,.xls"
        ref={fileInputRef}
        onChange={handleFileInputChange}
      />
    </Box>
  );
}