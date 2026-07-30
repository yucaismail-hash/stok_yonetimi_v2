// frontend/src/components/common/Hero.tsx
// Stokonomi Design System - Hero Component

import { Box, Typography, Chip, Stack, Avatar, Paper, Tooltip, Divider } from '@mui/material';
import { 
  Assessment, 
  Dataset,
  Inventory, 
  Schedule, 
  AutoAwesome,
  Psychology,
  CheckCircle,
  Pending,
} from '@mui/icons-material';

export interface HeroProps {
  title: string;
  subtitle?: string;
  datasetName?: string;
  productCount?: number;
  lastAnalysisDate?: string;
  aiReady?: boolean;
  aiStatus?: 'hazir' | 'bekleniyor' | 'hata';
  learningLevel?: string;
  learningScore?: number;
  learningComponents?: {  // ✅ YENİ EKLENDİ
    analysis_count?: { label: string };
    verified_rules?: { label: string };
    forecast_accuracy?: { label: string };
  };
  icon?: React.ReactNode;
  loading?: boolean;
}

export default function Hero({
  title,
  subtitle,
  datasetName = 'Aktif Dataset',
  productCount = 0,
  lastAnalysisDate,
  aiReady = false,
  aiStatus = 'bekleniyor',
  learningLevel = 'Başlangıç',
  learningScore = 0,
  learningComponents,  // ✅ YENİ EKLENDİ
  icon,
  loading = false,
}: HeroProps) {
  // ✅ AI Durumu metni ve rengi
  const getAIStatus = () => {
    if (loading) return { label: 'Yükleniyor...', color: 'default' as const };
    if (aiReady) return { label: '✅ AI Hazır', color: 'success' as const };
    if (aiStatus === 'hata') return { label: '⚠️ AI Hatası', color: 'error' as const };
    return { label: '⏳ AI Bekleniyor - Analiz yapın', color: 'default' as const };
  };

  const aiStatusInfo = getAIStatus();

  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: '#f8faff',
        border: '1px solid #e8f0fe',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 1.5,
        minHeight: 64,
      }}
    >
      {/* Sol: Sayfa Başlığı */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{ bgcolor: '#1f4e79', width: 36, height: 36 }}>
          {icon || <Assessment sx={{ fontSize: 18, color: 'white' }} />}
        </Avatar>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1rem', lineHeight: 1.2 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.65rem' }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>

      {/* Sağ: Metrikler */}
      <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Dataset */}
        <Chip
          icon={<Dataset sx={{ fontSize: 14 }} />}
          label={loading ? 'Yükleniyor...' : datasetName}
          size="small"
          variant="outlined"
          sx={{ height: 24, fontSize: '0.6rem' }}
        />

        {/* Ürün Sayısı */}
        <Chip
          icon={<Inventory sx={{ fontSize: 14 }} />}
          label={loading ? '...' : `${productCount} Ürün`}
          size="small"
          variant="outlined"
          sx={{ height: 24, fontSize: '0.6rem' }}
        />

        {/* Son Analiz */}
        {lastAnalysisDate && !loading && (
          <Chip
            icon={<Schedule sx={{ fontSize: 14 }} />}
            label={lastAnalysisDate}
            size="small"
            variant="outlined"
            sx={{ height: 24, fontSize: '0.6rem' }}
          />
        )}

        {/* AI Durumu */}
        <Chip
          icon={aiReady ? <CheckCircle sx={{ fontSize: 14 }} /> : <Pending sx={{ fontSize: 14 }} />}
          label={aiStatusInfo.label}
          size="small"
          color={aiStatusInfo.color}
          sx={{ 
            height: 24, 
            fontSize: '0.55rem', 
            fontWeight: 600,
            minWidth: aiReady ? 80 : 120,
          }}
        />

        {/* ✅ Learning Chip - Tooltip ile */}
        <Tooltip
          title={
            <Box sx={{ p: 1, maxWidth: 280 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#eff2f6', fontSize: '0.75rem', mb: 0.5 }}>
                Öğrenme Seviyesi: {learningLevel} ({learningScore}/100)
              </Typography>
              <Divider sx={{ mb: 0.5 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280' }}>📊 Analiz</Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#eff2f6', fontWeight: 500 }}>
                    {learningComponents?.analysis_count?.label || '0 analiz'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280' }}>✅ Kural</Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#eff2f6', fontWeight: 500 }}>
                    {learningComponents?.verified_rules?.label || '0 doğrulanmış kural'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280' }}>📈 Forecast</Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#eff2f6', fontWeight: 500 }}>
                    {learningComponents?.forecast_accuracy?.label || 'Forecast yok'}
                  </Typography>
                </Box>
              </Box>
            </Box>
          }
          arrow
          placement="bottom"
        >
          <Chip
            icon={<Psychology sx={{ fontSize: 14 }} />}
            label={loading ? '...' : `Öğrenme: ${learningLevel} (${learningScore})`}
            size="small"
            color={learningScore >= 60 ? 'success' : learningScore >= 40 ? 'warning' : 'default'}
            sx={{ 
              height: 24, 
              fontSize: '0.55rem', 
              fontWeight: 600,
              cursor: 'pointer',
              '&:hover': { opacity: 0.8 }
            }}
          />
        </Tooltip>
      </Stack>
    </Paper>
  );
}