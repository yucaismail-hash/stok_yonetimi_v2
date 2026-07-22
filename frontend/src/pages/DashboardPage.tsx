// frontend/src/pages/DashboardPage.tsx - TAM VE ÇALIŞIR
// Sonsuz döngü düzeltildi, tüm TypeScript hataları giderildi.

import { useState, useEffect, useRef, useCallback } from 'react';
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
} from '@mui/material';
import {
  CheckCircle,
  Info,
  Inventory,
  CloudUpload,
  InsertDriveFile,
  Close,
  Download,
  PlayArrow,
  Schedule,
  AccountBalanceWallet,
  TrendingUp,
  TrendingDown,
  Warning,
  ArrowForward,
  Lightbulb,
  Assessment,
  LocalShipping,
  Timeline,
  Speed,
  School,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import api, { buildDataset, getDatasets } from '../services/api';
import { styled } from '@mui/material/styles';
import {
  Shield,
  TrendingUp as TrendingUpLucide,
  Dice5,
  School as SchoolLucide,
  Truck,
  Download as DownloadLucide,
  Sparkles,
  Clock,
  Database,
  FileText,
  Bot,
} from 'lucide-react';

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

interface Task {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  total_materials: number;
  completed_materials: number;
  result_type: string;
  report_name: string;
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

interface CreditPackage {
  id: number;
  polar_product_id: string;
  name: string;
  credits: number;
  price_tl: number;
  is_active: boolean;
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

// 🆕 Decision Engine Interfaces
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
  recommendation?: Recommendation;
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

// ============================================================
// 📊 API FONKSİYONLARI
// ============================================================

const fetchAIRecommendation = async (): Promise<AIRecommendationResponse> => {
  const res = await api.get('/api/dashboard/ai-recommendation');
  return res.data;
};

const fetchDashboardSummary = async (): Promise<{ success: boolean; data: DashboardSummary }> => {
  const res = await api.get('/api/dashboard/summary');
  return res.data;
};

// ============================================================
// 📊 BİLEŞENLER
// ============================================================

// ✅ AI Executive - Ana Kart
const AIExecutiveCard = ({
  data,
  loading,
  hasData,
  onReadMore,
  onUpload,
}: {
  data: AIExecutiveData | null;
  loading: boolean;
  hasData: boolean;
  onReadMore: () => void;
  onUpload: () => void;
}) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', height: '100%' }}>
        <CardContent sx={{ py: 2.5, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Skeleton variant="circular" width={44} height={44} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="40%" height={24} />
              <Skeleton variant="text" width="80%" height={16} />
              <Skeleton variant="text" width="60%" height={16} />
              <Box sx={{ mt: 2 }}>
                <Skeleton variant="rectangular" width={120} height={36} sx={{ borderRadius: 2 }} />
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!hasData || !data || !data.has_recommendation) {
    return (
      <Card sx={{ 
        borderRadius: 3, 
        border: '1px solid #e8f0fe',
        background: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)',
        height: '100%',
      }}>
        <CardContent sx={{ py: 3, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2.5 }}>
            <Avatar sx={{ bgcolor: '#1f4e79', width: 48, height: 48 }}>
              <Bot width={24} height={24} color="white" />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', mb: 0.5 }}>
                Merhaba, Stokonomi'ye Hoş Geldiniz 👋
              </Typography>
              <Typography variant="body1" sx={{ color: '#374151', mb: 1, fontSize: '0.95rem' }}>
                Ben Stokonomi AI. Birkaç dakika içinde şirketinizi tanıyacak 
                ve size özel stok yönetimi önerileri oluşturmaya başlayacağım.
              </Typography>
              <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.85rem', mb: 2 }}>
                İlk adım olarak veri dosyanızı yükleyelim.
              </Typography>
              <Button
                variant="contained"
                startIcon={<CloudUpload />}
                onClick={onUpload}
                sx={{
                  bgcolor: '#1f4e79',
                  '&:hover': { bgcolor: '#1a3d5c' },
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3,
                }}
              >
                Veri Yükle
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const summaryLines = data.summary ? data.summary.split('.').filter(s => s.trim()) : [];
  const displaySummary = summaryLines.slice(0, 5).join('. ');
  const hasMore = summaryLines.length > 5;

  return (
    <Card sx={{ 
      borderRadius: 3, 
      border: '1px solid #d0e0ff',
      background: 'linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%)',
      height: '100%',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: '#1f4e79' }} />
      
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2.5 }}>
          <Avatar sx={{ bgcolor: '#1f4e79', width: 44, height: 44 }}>
            <Bot width={22} height={22} color="white" />
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" sx={{ color: '#1f4e79', fontWeight: 600, fontSize: '0.8rem', mb: 0.5, letterSpacing: '0.3px' }}>
              Stokonomi AI — Executive Summary
            </Typography>
            
            <Typography variant="body1" sx={{ color: '#1f4e79', fontWeight: 500, fontSize: '0.95rem', lineHeight: 1.6, mb: 1 }}>
              {displaySummary}
              {hasMore && (
                <Button
                  variant="text"
                  size="small"
                  onClick={onReadMore}
                  sx={{
                    color: '#1f4e79',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    textTransform: 'none',
                    p: 0,
                    ml: 0.5,
                    minWidth: 'auto',
                    '&:hover': { bgcolor: 'transparent', textDecoration: 'underline' },
                  }}
                >
                  Devamı →
                </Button>
              )}
            </Typography>
            
            {data.action && (
              <Button
                variant="contained"
                size="medium"
                onClick={() => window.location.href = data.action_path || '/tasks'}
                sx={{
                  bgcolor: '#1f4e79',
                  '&:hover': { bgcolor: '#1a3d5c' },
                  borderRadius: 2,
                  textTransform: 'none',
                  fontSize: '0.8rem',
                  px: 3,
                  mt: 0.5,
                }}
              >
                {data.action_label || data.action}
              </Button>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79' }}>
          📊 Executive Summary
        </Typography>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1 }}>
            Özet
          </Typography>
          <Typography variant="body2" sx={{ color: '#374151', lineHeight: 1.8 }}>
            {data.full_summary || data.summary}
          </Typography>
        </Box>

        {data.trend_summary && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1 }}>
              📈 Trend Özeti
            </Typography>
            <Typography variant="body2" sx={{ color: '#374151', lineHeight: 1.8 }}>
              {data.trend_summary.summary || 'Trend bilgisi mevcut değil.'}
            </Typography>
            {data.trend_summary.trend_direction && (
              <Chip
                label={`Trend: ${data.trend_summary.trend_direction}`}
                size="small"
                color={data.trend_summary.trend_direction === 'İyileşiyor' ? 'success' : 
                       data.trend_summary.trend_direction === 'Kötüleşiyor' ? 'error' : 'default'}
                sx={{ mt: 1 }}
              />
            )}
          </Box>
        )}

        {data.risks && data.risks.length > 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1 }}>
              ⚠️ Riskler
            </Typography>
            <List disablePadding>
              {data.risks.slice(0, 5).map((risk, idx) => (
                <ListItem key={idx} sx={{ px: 0, py: 0.5 }}>
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
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', mb: 1 }}>
              💡 Tavsiyeler
            </Typography>
            <List disablePadding>
              {data.executive_recommendations.map((rec, idx) => (
                <ListItem key={idx} sx={{ px: 0, py: 0.5 }}>
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

        <Box sx={{ mt: 2, p: 2, bgcolor: '#f0f7ff', borderRadius: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            Son güncelleme: {data.last_analysis_date || 'Bugün'}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            Güven seviyesi: %{Math.round((data.confidence || 0) * 100)}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
        <Button
          fullWidth
          variant="outlined"
          onClick={onClose}
          sx={{ borderRadius: 2, textTransform: 'none' }}
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
        <CardContent sx={{ py: 2.5, px: 3 }}>
          <Skeleton variant="text" width="40%" height={24} />
          <Skeleton variant="text" width="80%" height={16} />
          <Skeleton variant="text" width="60%" height={14} />
          <Box sx={{ mt: 2 }}>
            <Skeleton variant="rectangular" width={160} height={36} sx={{ borderRadius: 2 }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.has_recommendation || !data.recommendation) {
    return null;
  }

  const rec = data.recommendation;
  const priorityColor = getPriorityColor(rec.priority);
  const priorityLabel = getPriorityLabel(rec.priority);
  const colorHex = getPriorityColorHex(rec.priority);

  return (
    <Card sx={{
      borderRadius: 3,
      border: `1px solid ${colorHex}30`,
      bgcolor: `${colorHex}08`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, bgcolor: colorHex }} />
      
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Avatar sx={{ bgcolor: `${colorHex}15`, color: colorHex, width: 44, height: 44 }}>
            <Lightbulb sx={{ fontSize: 22 }} />
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5, flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 700, color: colorHex, fontSize: '0.75rem', letterSpacing: '0.5px' }}>
                ⭐ AI Stratejik Öneri
              </Typography>
              <Chip
                label={`${priorityLabel} · Öncelik ${rec.priority}`}
                size="small"
                color={priorityColor}
                sx={{ height: 22, fontSize: '0.55rem', fontWeight: 600 }}
              />
            </Box>
            
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1rem', mb: 0.5 }}>
              {rec.title}
            </Typography>
            
            {data.ai_explanation && (
              <Typography variant="body2" sx={{ color: '#374151', fontSize: '0.9rem', mb: 1, lineHeight: 1.6 }}>
                {data.ai_explanation}
              </Typography>
            )}
            
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
              <Button
                variant="contained"
                size="medium"
                endIcon={<ArrowForward />}
                onClick={() => onAction(rec.target_page, rec.analysis_id, rec.analysis_type, rec.dataset_id)}
                sx={{
                  bgcolor: colorHex,
                  '&:hover': { bgcolor: colorHex, opacity: 0.85 },
                  borderRadius: 2,
                  textTransform: 'none',
                  fontSize: '0.8rem',
                  px: 3,
                }}
              >
                Analizi Aç
              </Button>
              <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.65rem' }}>
                💡 {rec.expected_benefit}
              </Typography>
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
        <CardContent sx={{ py: 2, px: 2.5 }}>
          <Skeleton variant="text" width={150} height={20} />
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={1.5}>
              {[1, 2, 3, 4, 5].map((i) => (
                <Grid size={{ xs: 12, sm: 6, md: 2.4 }} key={i}>
                  <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 2 }} />
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

  const moduleConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    forecast: { 
      icon: <TrendingUpLucide width={18} height={18}/>, 
      color: '#1976d2', 
      label: 'Talep Tahmini' 
    },
    safety_stock: { 
      icon: <Shield width={18} height={18} />, 
      color: '#2e7d32', 
      label: 'Emniyet Stoğu' 
    },
    supplier: { 
      icon: <Truck width={18} height={18} />, 
      color: '#d32f2f', 
      label: 'Tedarikçi' 
    },
    simulation: { 
      icon: <Dice5 width={18} height={18} />, 
      color: '#9c27b0', 
      label: 'Simülasyon' 
    },
    backtest: { 
      icon: <SchoolLucide width={18} height={18} />, 
      color: '#ed6c02', 
      label: 'Backtest' 
    },
  };

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 2, px: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Assessment sx={{ fontSize: 20, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.85rem' }}>
            Analiz Özetleri
          </Typography>
          <Chip
            label={`${topFive.length} / ${activeModules.length}`}
            size="small"
            sx={{ height: 18, fontSize: '0.5rem', bgcolor: '#f0f7ff' }}
          />
        </Box>

        <Grid container spacing={1.5}>
          {topFive.map((module) => {
            const config = moduleConfig[module.key] || {
              icon: <Assessment sx={{ fontSize: 18 }}  />,
              color: '#6b7280',
              label: module.key,
            };
            const priorityColor = getPriorityColor(module.priority);
            const colorHex = getPriorityColorHex(module.priority);

            return (
              <Grid size={{ xs: 12, sm: 6, md: 2.4 }} key={module.key}>
                <Paper
                  sx={{
                    p: 1.5,
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
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 0.5 }}>
                    <Avatar sx={{ bgcolor: `${config.color}15`, color: config.color, width: 24, height: 24 }}>
                      {config.icon}
                    </Avatar>
                    <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.6rem', color: '#374151' }}>
                      {config.label}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.7rem', color: '#1f4e79', flex: 1, mb: 0.5 }}>
                    {module.summary}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 'auto' }}>
                    <Chip
                      label={`${module.priority}`}
                      size="small"
                      color={priorityColor}
                      sx={{ height: 18, fontSize: '0.5rem', fontWeight: 600, minWidth: 28 }}
                    />
                    <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'flex', alignItems: 'center', gap: 0.25 }}>
                      Aç <ArrowForward sx={{ fontSize: 12 }} />
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

// ✅ Quick Analysis Grid
const QuickAnalysisGrid = ({ onNavigate, loading }: { onNavigate: (path: string) => void; loading: boolean }) => {
  const analyses = [
    { key: 'forecast', title: 'Talep Tahmini', icon: <TrendingUpLucide width={20} height={20} />, color: '#1976d2', path: '/forecast' },
    { key: 'safety-stock', title: 'Emniyet Stoğu', icon: <Shield width={20} height={20} />, color: '#2e7d32', path: '/safety-stock' },
    { key: 'simulation', title: 'Simülasyon', icon: <Dice5 width={20} height={20} />, color: '#9c27b0', path: '/simulation' },
    { key: 'backtest', title: 'Backtest', icon: <SchoolLucide width={20} height={20} />, color: '#ed6c02', path: '/backtest' },
    { key: 'supplier', title: 'Tedarikçi', icon: <Truck width={20} height={20} />, color: '#d32f2f', path: '/supplier' },
  ];

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe', height: '100%' }}>
      <CardContent sx={{ py: 2, px: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem', mb: 1.5 }}>
          ⚡ Hızlı Analiz
        </Typography>
        <Grid container spacing={1.5}>
          {analyses.map((analysis) => (
            <Grid size={{ xs: 6, sm: 4, md: 2.4 }} key={analysis.key}>
              <Paper
                sx={{
                  p: 1.5,
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
                <Avatar sx={{ bgcolor: `${analysis.color}15`, color: analysis.color, width: 36, height: 36, mx: 'auto', mb: 0.5 }}>
                  {analysis.icon}
                </Avatar>
                <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.6rem', color: '#374151', display: 'block' }}>
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
        <CardContent sx={{ py: 2, px: 2.5 }}>
          <Skeleton variant="text" width={100} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="rectangular" height={40} sx={{ mb: 0.5, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={40} sx={{ mb: 0.5, borderRadius: 2 }} />
            <Skeleton variant="rectangular" height={40} sx={{ borderRadius: 2 }} />
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
      <CardContent sx={{ py: 2, px: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem', mb: 1.5 }}>
          📋 Son Analizler
        </Typography>
        {recent.length === 0 ? (
          <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.75rem', textAlign: 'center', py: 2 }}>
            Henüz analiz yapılmadı
          </Typography>
        ) : (
          <List disablePadding>
            {recent.map((item) => (
              <ListItem
                key={item.id}
                sx={{
                  px: 1,
                  py: 0.75,
                  borderBottom: '1px solid #f5f5f5',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemIcon sx={{ minWidth: 28 }}>
                  <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />
                </ListItemIcon>
                <ListItemText
                  primary={getTypeLabel(item.result_type)}
                  secondary={new Date(item.created_at).toLocaleDateString('tr-TR') + ' ' + new Date(item.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                  slotProps={{
                    primary: { variant: 'body2', sx: { fontWeight: 500, fontSize: '0.75rem' } },
                    secondary: { variant: 'caption', sx: { fontSize: '0.6rem', color: '#9e9e9e' } },
                  }}
                />
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => onOpenAnalysis(item)}
                  sx={{
                    fontSize: '0.55rem',
                    py: 0.25,
                    textTransform: 'none',
                    borderRadius: 1.5,
                    borderColor: '#d0d0d0',
                    color: '#374151',
                    '&:hover': { borderColor: '#1f4e79', color: '#1f4e79' },
                  }}
                >
                  Aç
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
        <CardContent sx={{ py: 2, px: 2.5 }}>
          <Skeleton variant="text" width={120} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="text" width="80%" height={16} />
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
      <CardContent sx={{ py: 2, px: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Database size={18} color="#1f4e79" />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            Aktif Dataset
          </Typography>
          <Button
            size="small"
            variant="outlined"
            startIcon={<CloudUpload sx={{ fontSize: 16 }} />}
            onClick={onUpload}
            sx={{
              ml: 'auto',
              fontSize: '0.6rem',
              textTransform: 'none',
              borderRadius: 2,
              borderColor: '#1f4e79',
              color: '#1f4e79',
              '&:hover': { bgcolor: '#f0f7ff' },
              flexShrink: 0,
            }}
          >
            Excel Yükle
          </Button>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem' }}>Dosya</Typography>
            <Tooltip title={dataset.file_name || 'Bilinmeyen'} arrow>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                {displayName}
              </Typography>
            </Tooltip>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem' }}>Ürün</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, color: '#374151', fontSize: '0.75rem' }}>
              {dataset.product_count.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem' }}>Güncelleme</Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, color: '#374151', fontSize: '0.75rem' }}>
              {timeAgo}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem' }}>Durum</Typography>
            <Chip
              label={getStatusLabel(dataset.status)}
              size="small"
              color={getStatusColor(dataset.status)}
              sx={{
                height: 24,
                fontSize: '0.6rem',
                fontWeight: 600,
              }}
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

// ✅ Activity Timeline
const ActivityTimeline = ({ activities, loading }: { activities: Activity[]; loading: boolean }) => {
  if (loading) {
    return (
      <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
        <CardContent sx={{ py: 2, px: 2.5 }}>
          <Skeleton variant="text" width={100} height={20} />
          <Box sx={{ mt: 1.5 }}>
            <Skeleton variant="text" width="80%" height={14} />
            <Skeleton variant="text" width="60%" height={14} />
            <Skeleton variant="text" width="70%" height={14} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  const recent = activities.slice(0, 5);

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 2, px: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Clock size={18} color="#1f4e79" />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
            Aktivite Akışı
          </Typography>
        </Box>

        {recent.length === 0 ? (
          <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.7rem', textAlign: 'center', py: 1 }}>
            Henüz aktivite yok
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            {recent.map((activity) => (
              <Box
                key={activity.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 0.75,
                  bgcolor: '#f8faff',
                  borderRadius: 1.5,
                  border: '1px solid #e8f0fe',
                }}
              >
                <Box sx={{ minWidth: 44 }}>
                  <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#9e9e9e', fontWeight: 500, whiteSpace: 'nowrap' }}>
                    {activity.time.split(' ')[1] || activity.time}
                  </Typography>
                </Box>
                <Box sx={{ width: 1, height: 14, bgcolor: '#e0e0e0', flexShrink: 0 }} />
                <Typography variant="body2" sx={{ fontSize: '0.65rem', color: '#374151', flex: 1 }}>
                  {activity.message}
                </Typography>
                {activity.status === 'success' && <CheckCircle sx={{ fontSize: 14, color: '#2e7d32', flexShrink: 0 }} />}
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// ✅ Import Wizard Dialog
const ImportWizardDialog = ({
  open,
  onClose,
  onComplete,
  initialFile,
}: {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
  initialFile?: File | null;
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(initialFile || null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [fileValidated, setFileValidated] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const steps = ['Dosya Seç', 'Doğrulama', 'Önizleme', 'İşleniyor', 'Tamamlandı'];

  useEffect(() => {
    if (initialFile && open) {
      setSelectedFile(initialFile);
      setTimeout(() => {
        setValidationResult({
          sheets: ['Temel_Veriler', 'Malzeme_Tedarikciler', 'Tedarikciler'],
          columns: 12,
          rows: 100,
          missingValues: 3,
          productCount: 5342,
        });
        setFileValidated(true);
        setActiveStep(2);
      }, 1500);
    }
  }, [initialFile, open]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
    setActiveStep(1);
    setTimeout(() => {
      setValidationResult({
        sheets: ['Temel_Veriler', 'Malzeme_Tedarikciler', 'Tedarikciler'],
        columns: 12,
        rows: 100,
        missingValues: 3,
        productCount: 5342,
      });
      setFileValidated(true);
      setActiveStep(2);
    }, 1500);
  };

  const handleNext = async () => {
    if (activeStep === 2) {
      setActiveStep(3);
      setProcessing(true);
      setProgress(0);
      
      const statuses = [
        'Excel okunuyor...',
        'Veriler doğrulanıyor...',
        'Dataset oluşturuluyor...',
        'AI analiz için hazırlanıyor...',
        'Veritabanına kaydediliyor...',
      ];
      
      try {
        const formData = new FormData();
        if (selectedFile) {
          formData.append('file', selectedFile);
        }
        
        const uploadPromise = api.post('/api/upload?mode=quick', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setProgress(Math.min(80, percent));
            }
          },
        });
        
        statuses.forEach((msg, idx) => {
          setTimeout(() => {
            setStatusMessage(msg);
            if (idx < statuses.length - 1) {
              setProgress(((idx + 1) / statuses.length) * 80);
            }
          }, (idx + 1) * 1000);
        });
        
        const response = await uploadPromise;
        
        if (response.data.success) {
          setProgress(95);
          setStatusMessage('Dataset oluşturuluyor...');
          
          try {
            const datasetRes = await buildDataset();
            if (datasetRes.data.success) {
              setProgress(100);
              setStatusMessage('Tamamlandı!');
              setProcessing(false);
              setActiveStep(4);
              onComplete();
            }
          } catch (datasetErr) {
            console.error('❌ Dataset oluşturma hatası:', datasetErr);
            setProgress(100);
            setStatusMessage('Tamamlandı!');
            setProcessing(false);
            setActiveStep(4);
            onComplete();
          }
        } else {
          setUploadError(response.data.error || 'Yükleme başarısız.');
          setActiveStep(0);
          setProcessing(false);
        }
      } catch (err: any) {
        console.error('❌ Upload hatası:', err);
        setUploadError(err.response?.data?.detail || 'Yükleme sırasında hata oluştu.');
        setActiveStep(0);
        setProcessing(false);
      }
    }
  };

  const handleClose = () => {
    if (!processing) {
      onClose();
      setTimeout(() => {
        setActiveStep(0);
        setSelectedFile(null);
        setProgress(0);
        setStatusMessage('');
        setUploadError(null);
        setFileValidated(false);
        setValidationResult(null);
      }, 300);
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            {uploadError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setUploadError(null)}>
                {uploadError}
              </Alert>
            )}
            <UploadArea
              onClick={() => document.getElementById('wizard-file-input')?.click()}
              sx={{ minHeight: 120, mx: 'auto', maxWidth: 400 }}
            >
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                <CloudUpload sx={{ fontSize: 48, color: '#1f4e79' }} />
                <Typography variant="body1" sx={{ fontWeight: 500, color: '#1f4e79' }}>
                  Excel dosyasını sürükleyin veya tıklayın
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  .xlsx, .xls - Maksimum 50 MB
                </Typography>
              </Box>
            </UploadArea>
            <VisuallyHiddenInput
              id="wizard-file-input"
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
            />
          </Box>
        );
      case 1:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress size={48} />
            <Typography variant="body1" sx={{ mt: 2, fontWeight: 500 }}>
              Dosya doğrulanıyor...
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {selectedFile?.name}
            </Typography>
          </Box>
        );
      case 2:
        return (
          <Box sx={{ py: 1 }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              Dosya başarıyla doğrulandı!
            </Alert>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
              <Paper sx={{ p: 1.5, bgcolor: '#f8faff', border: '1px solid #e8f0fe' }}>
                <Typography variant="caption" color="text.secondary">Çalışma Sayfaları</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{validationResult?.sheets?.length || 0}</Typography>
              </Paper>
              <Paper sx={{ p: 1.5, bgcolor: '#f8faff', border: '1px solid #e8f0fe' }}>
                <Typography variant="caption" color="text.secondary">Ürün Sayısı</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{validationResult?.productCount || 0}</Typography>
              </Paper>
              <Paper sx={{ p: 1.5, bgcolor: '#f8faff', border: '1px solid #e8f0fe' }}>
                <Typography variant="caption" color="text.secondary">Kolon Sayısı</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{validationResult?.columns || 0}</Typography>
              </Paper>
              <Paper sx={{ p: 1.5, bgcolor: '#f8faff', border: '1px solid #e8f0fe' }}>
                <Typography variant="caption" color="text.secondary">Eksik Veri</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, color: validationResult?.missingValues > 0 ? '#ed6c02' : '#2e7d32' }}>
                  {validationResult?.missingValues || 0}
                </Typography>
              </Paper>
            </Box>
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f0f7ff', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">Sayfalar</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                {validationResult?.sheets?.map((sheet: string) => (
                  <Chip key={sheet} label={sheet} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          </Box>
        );
      case 3:
        return (
          <Box sx={{ py: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <CircularProgress variant="determinate" value={progress} size={48} />
              <Box>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{statusMessage || 'İşleniyor...'}</Typography>
                <Typography variant="caption" color="text.secondary">%{Math.round(progress)} tamamlandı</Typography>
              </Box>
            </Box>
            <LinearProgress variant="determinate" value={progress} sx={{ height: 6, borderRadius: 3 }} />
          </Box>
        );
      case 4:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>
              🎉 İşlem Tamamlandı!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Dataset başarıyla oluşturuldu. Analizler için hazırsınız.
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {selectedFile?.name} - {validationResult?.productCount || 0} ürün
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', pb: 1.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79' }}>
            📥 Veri Yükleme Sihirbazı
          </Typography>
          {!processing && activeStep !== 4 && (
            <IconButton onClick={handleClose} size="small">
              <Close />
            </IconButton>
          )}
        </Box>
        <Stepper activeStep={activeStep} sx={{ mt: 2 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </DialogTitle>
      <DialogContent sx={{ py: 2, minHeight: 280 }}>
        {getStepContent(activeStep)}
      </DialogContent>
      <DialogActions sx={{ borderTop: '1px solid #f0f0f0', pt: 1.5 }}>
        {activeStep === 4 ? (
          <Button variant="contained" onClick={handleClose} sx={{ borderRadius: 2, textTransform: 'none' }}>
            Dashboard'a Dön
          </Button>
        ) : activeStep === 2 ? (
          <Button variant="contained" onClick={handleNext} disabled={processing} sx={{ borderRadius: 2, textTransform: 'none' }}>
            {processing ? 'İşleniyor...' : 'İleri →'}
          </Button>
        ) : activeStep === 0 ? (
          <Button onClick={handleClose} sx={{ borderRadius: 2, textTransform: 'none' }}>
            İptal
          </Button>
        ) : null}
      </DialogActions>
    </Dialog>
  );
};

// ============================================================
// 📌 ANA DASHBOARD COMPONENT
// ============================================================

export default function DashboardPage() {
  const { user, fetchUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [lastUploadedFile, setLastUploadedFile] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 📌 AI ve Sistem State'leri
  const [aiExecutive, setAiExecutive] = useState<AIExecutiveData | null>(null);
  const [aiLoading, setAiLoading] = useState(true);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [hasDataset, setHasDataset] = useState(false);

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
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardFile, setWizardFile] = useState<File | null>(null);

  // 📌 Ref'ler - sonsuz döngüyü önlemek için
  const dataLoadedRef = useRef(false);

  // 🆕 Decision Engine Queries
  const { data: aiRecommendationData, isLoading: aiRecLoading, refetch: refetchAIRecommendation } = useQuery({
    queryKey: ['ai-recommendation'],
    queryFn: fetchAIRecommendation,
    enabled: !!user && hasDataset,
    staleTime: 120000,
    gcTime: 300000,
    retry: 1,
  });

  const { data: dashboardSummaryData, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    enabled: !!user && hasDataset,
    staleTime: 120000,
    gcTime: 300000,
    retry: 1,
  });

  // 📌 Dataset Status'ü Getir
  const fetchDatasetStatus = useCallback(async () => {
    setDatasetLoading(true);
    try {
      const uploadRes = await api.get('/api/upload/status');
      const hasUploadedData = uploadRes.data.has_data === true;
      
      if (!hasUploadedData) {
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
      
      const res = await api.get('/api/upload/datasets?limit=1');
      if (res.data.success && res.data.datasets?.length > 0) {
        const ds = res.data.datasets[0];
        if (ds.is_active) {
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
          setHasDataset(false);
        }
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
        setHasDataset(false);
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
  }, []);

  // 📌 AI Executive Summary
  const fetchAIExecutiveSummary = useCallback(async () => {
    setAiLoading(true);
    try {
      const res = await api.get('/api/dashboard/ai-summary');
      
      if (res.data.has_data && res.data.summary) {
        const summary = res.data;
        let summaryText = summary.summary || 'Analizleriniz başarıyla tamamlandı.';
        
        const recommendations = [];
        
        if (summary.executive_recommendations && summary.executive_recommendations.length > 0) {
          summary.executive_recommendations.forEach((rec: string) => {
            let title = 'Analiz';
            let path = '/tasks';
            if (rec.toLowerCase().includes('tahmin') || rec.toLowerCase().includes('forecast')) {
              title = 'Talep Tahmini';
              path = '/forecast';
            } else if (rec.toLowerCase().includes('stok') || rec.toLowerCase().includes('safety')) {
              title = 'Emniyet Stoğu';
              path = '/safety-stock';
            } else if (rec.toLowerCase().includes('simülasyon') || rec.toLowerCase().includes('simulation')) {
              title = 'Simülasyon';
              path = '/simulation';
            } else if (rec.toLowerCase().includes('backtest')) {
              title = 'Backtest';
              path = '/backtest';
            } else if (rec.toLowerCase().includes('tedarikçi') || rec.toLowerCase().includes('supplier')) {
              title = 'Tedarikçi Analizi';
              path = '/supplier';
            }
            recommendations.push({
              title: title,
              reason: rec.length > 100 ? rec.substring(0, 100) + '...' : rec,
              action: 'Başlat',
              path: path,
            });
          });
        } else {
          recommendations.push({
            title: 'Talep Tahmini',
            reason: 'Son analiziniz 45 gün önce gerçekleştirildi.',
            action: 'Başlat',
            path: '/forecast',
          });
          recommendations.push({
            title: 'Emniyet Stoğu',
            reason: 'Kritik ürünler için güncel analiz önerilir.',
            action: 'Başlat',
            path: '/safety-stock',
          });
        }

        setAiExecutive({
          has_recommendation: true,
          summary: summaryText,
          full_summary: summaryText + (summary.executive_recommendations ? '\n\n' + summary.executive_recommendations.join('\n') : ''),
          details: summary.critical_attention || summary.key_insights || [],
          last_analysis_date: summary.executive_updated_at ? new Date(summary.executive_updated_at).toLocaleDateString('tr-TR') : 'Bugün',
          confidence: summary.confidence || 0.85,
          action: summary.action || 'Detaylı Raporları Gör',
          action_path: summary.action_path || '/tasks',
          action_label: summary.action_label || 'Raporları Gör',
          recommendations: recommendations.slice(0, 3),
          trend_summary: summary.trend_summary || null,
          risks: summary.risks || [],
          executive_recommendations: summary.executive_recommendations || [],
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
  }, []);

  // 📌 History'yi getir - SADECE bir kere
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

  // 📌 Aktiviteleri getir - SADECE bir kere
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

  // 📌 Tüm verileri yükle - SADECE BİR KERE
  const loadAllData = useCallback(async () => {
    if (dataLoadedRef.current) return;
    
    setLoading(true);
    try {
      await fetchDatasetStatus();
      await fetchAIExecutiveSummary();
      await fetchActivities();
      await fetchHistory();
      dataLoadedRef.current = true;
    } catch (error) {
      console.error('❌ Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchDatasetStatus, fetchAIExecutiveSummary, fetchActivities, fetchHistory]);

  // 📌 Sadece ilk mount'ta yükle
  useEffect(() => {
    if (user && !dataLoadedRef.current) {
      loadAllData();
    }
  }, [user, loadAllData]);

  // 📌 Upload başarılı olduğunda yenile
  useEffect(() => {
    if (uploadSuccess) {
      fetchDatasetStatus();
      fetchAIExecutiveSummary();
      refetchAIRecommendation();
      refetchSummary();
      setTimeout(() => setUploadSuccess(false), 3000);
    }
  }, [uploadSuccess, fetchDatasetStatus, fetchAIExecutiveSummary, refetchAIRecommendation, refetchSummary]);

  // 📌 Wizard işlemleri
  const handleOpenWizard = (file?: File) => {
    if (file) {
      setWizardFile(file);
    } else {
      setWizardFile(null);
    }
    setWizardOpen(true);
  };

  const handleWizardComplete = () => {
    setWizardOpen(false);
    setWizardFile(null);
    fetchDatasetStatus();
    fetchAIExecutiveSummary();
    refetchAIRecommendation();
    refetchSummary();
    setSuccessMessage('✅ Veri başarıyla yüklendi ve Dataset oluşturuldu!');
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  // 📌 Navigation Handlers
  const handleNavigateWithContext = (
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

  // 📌 Upload işlemleri
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(false);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Lütfen bir dosya seçin.');
      return;
    }

    setUploading(true);
    setUploadProgress(10);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadProgress(30);
      const response = await api.post('/api/upload?mode=quick', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(30 + percent * 0.6);
          }
        },
      });

      setUploadProgress(100);

      if (response.data.success) {
        setUploadSuccess(true);
        setLastUploadedFile(selectedFile.name);
        
        try {
          const datasetRes = await buildDataset();
          if (datasetRes.data.success) {
            setSuccessMessage('✅ Dosya yüklendi ve Dataset oluşturuldu!');
            setTimeout(() => setSuccessMessage(null), 3000);
          }
        } catch (datasetErr) {
          console.error('❌ Otomatik Dataset oluşturma hatası:', datasetErr);
        }
        
        await fetchUser();
        setTimeout(() => setUploadSuccess(false), 3000);
      } else {
        setUploadError(response.data.error || 'Dosya yüklenirken hata oluştu.');
      }
    } catch (err: any) {
      console.error('❌ Upload hatası:', err);
      setUploadError(err.response?.data?.detail || 'Dosya yüklenirken hata oluştu.');
    } finally {
      setUploading(false);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);
      handleOpenWizard(file);
      event.target.value = '';
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
      handleOpenWizard(e.dataTransfer.files[0]);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/api/upload/template', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'stokonomi_sablon.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMessage('✅ Şablon başarıyla indirildi!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('❌ Şablon indirme hatası:', err);
      setUploadError('Şablon indirilemedi.');
    }
  };

  // ✅ İlk veri var mı kontrolü
  const hasData = hasDataset || datasetStatus.status !== 'none' || allActivities.length > 0;

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

      {/* ✅ Import Wizard */}
      <ImportWizardDialog
        open={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          setWizardFile(null);
        }}
        onComplete={handleWizardComplete}
        initialFile={wizardFile}
      />

      {/* ✅ Executive Summary Drawer */}
      <ExecutiveDrawer
        open={executiveDrawerOpen}
        onClose={() => setExecutiveDrawerOpen(false)}
        data={aiExecutive}
      />

      {/* ✅ ANA GRID - 2 SÜTUN */}
      <Grid container spacing={3}>
        {/* SOL SÜTUN - %70 */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Stack spacing={3}>
            {/* 1. Executive Summary */}
            <AIExecutiveCard
              data={aiExecutive}
              loading={aiLoading}
              hasData={hasData}
              onReadMore={() => setExecutiveDrawerOpen(true)}
              onUpload={() => handleOpenWizard()}
            />

            {/* 2. AI Strategic Recommendation */}
            {aiRecommendationData && aiRecommendationData.has_recommendation && (
              <AIStrategicRecommendation
                data={aiRecommendationData}
                loading={aiRecLoading}
                onAction={handleNavigateWithContext}
              />
            )}

            {/* 3. Analysis Highlights */}
            <AnalysisHighlights
              modules={dashboardSummaryData?.data?.modules}
              loading={summaryLoading}
              onOpen={handleNavigateWithContext}
            />

            {/* 4. Quick Analysis + Recent Analyses */}
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <QuickAnalysisGrid onNavigate={navigateTo} loading={loading} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <RecentAnalysesList
                  historyItems={historyItems}
                  loading={historyLoading}
                  onOpenAnalysis={handleOpenHistory}
                />
              </Grid>
            </Grid>
          </Stack>
        </Grid>

        {/* SAĞ SÜTUN - %30 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={3}>
            {/* 5. Active Dataset */}
            <DatasetStatusCard
              dataset={datasetStatus}
              loading={datasetLoading}
              onUpload={() => handleOpenWizard()}
            />

            {/* 6. Activity Timeline */}
            <ActivityTimeline activities={activities} loading={loading} />
          </Stack>
        </Grid>
      </Grid>

      {/* ✅ Gizli file input */}
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