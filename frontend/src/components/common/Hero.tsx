// frontend/src/components/common/Hero.tsx
// Stokonomi Design System - Hero Component

import { Box, Typography, Chip, Stack, Avatar, Paper } from '@mui/material';
import { 
  Assessment, 
  Dataset,
  Inventory, 
  Schedule, 
  AutoAwesome,
  Psychology 
} from '@mui/icons-material';

// ✅ interface'i export et
export interface HeroProps {
  title: string;
  subtitle?: string;
  datasetName?: string;
  productCount?: number;
  lastAnalysisDate?: string;
  aiReady?: boolean;
  learningLevel?: string;
  learningScore?: number;
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
  learningLevel = 'Başlangıç',
  learningScore = 0,
  icon,
}: HeroProps) {
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
      <Stack 
        direction="row" 
        spacing={1.5} 
        sx={{ flexWrap: 'wrap', alignItems: 'center' }}  // ✅ alignItems doğrudan Stack'e değil, sx içinde
      >
        {/* Dataset */}
        <Chip
          icon={<Dataset sx={{ fontSize: 14 }} />}  // ✅ Database → Dataset
          label={datasetName}
          size="small"
          variant="outlined"
          sx={{ height: 24, fontSize: '0.6rem' }}
        />

        {/* Ürün Sayısı */}
        <Chip
          icon={<Inventory sx={{ fontSize: 14 }} />}
          label={`${productCount} Ürün`}
          size="small"
          variant="outlined"
          sx={{ height: 24, fontSize: '0.6rem' }}
        />

        {/* Son Analiz */}
        {lastAnalysisDate && (
          <Chip
            icon={<Schedule sx={{ fontSize: 14 }} />}
            label={lastAnalysisDate}
            size="small"
            variant="outlined"
            sx={{ height: 24, fontSize: '0.6rem' }}
          />
        )}

        {/* AI Hazır */}
        <Chip
          icon={<AutoAwesome sx={{ fontSize: 14 }} />}
          label={aiReady ? 'AI Hazır' : 'AI Bekleniyor'}
          size="small"
          color={aiReady ? 'success' : 'default'}
          sx={{ height: 24, fontSize: '0.55rem', fontWeight: 600 }}
        />

        {/* Learning Durumu */}
        <Chip
          icon={<Psychology sx={{ fontSize: 14 }} />}
          label={`Öğrenme: ${learningLevel} (${learningScore})`}
          size="small"
          color={learningScore >= 60 ? 'success' : learningScore >= 40 ? 'warning' : 'default'}
          sx={{ height: 24, fontSize: '0.55rem', fontWeight: 600 }}
        />
      </Stack>
    </Paper>
  );
}