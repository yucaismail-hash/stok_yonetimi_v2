// frontend/src/components/Dashboard/LearningScoreBadge.tsx
// Learning Score Badge - Dashboard'da gösterilen öğrenme seviyesi

import { Box, Typography, Chip, CircularProgress, Tooltip, Paper, Skeleton } from '@mui/material';
import { useLearningScore } from '../../hooks/useLearningScore';
import { TrendingUp, School, AutoAwesome } from '@mui/icons-material';

interface LearningScoreBadgeProps {
  variant?: 'compact' | 'full';
  showDetails?: boolean;
}

const getLevelColor = (level: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (level) {
    case 'Uzman': return 'success';
    case 'İleri': return 'info';
    case 'Orta': return 'warning';
    case 'Başlangıç': return 'default';
    case 'Öğreniyor': return 'default';
    default: return 'default';
  }
};

const getLevelIcon = (level: string) => {
  switch (level) {
    case 'Uzman': return <AutoAwesome sx={{ fontSize: 14 }} />;
    case 'İleri': return <TrendingUp sx={{ fontSize: 14 }} />;
    case 'Orta': return <School sx={{ fontSize: 14 }} />;
    case 'Başlangıç': return <School sx={{ fontSize: 14 }} />;
    case 'Öğreniyor': return <School sx={{ fontSize: 14 }} />;
    default: return <School sx={{ fontSize: 14 }} />;
  }
};

export default function LearningScoreBadge({ variant = 'compact', showDetails = false }: LearningScoreBadgeProps) {
  const { data: scoreData, isLoading, isError } = useLearningScore();

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={16} />
        <Typography variant="caption" color="text.secondary">Öğrenme skoru hesaplanıyor...</Typography>
      </Box>
    );
  }

  if (isError || !scoreData) {
    return (
      <Chip
        label="Öğrenme: -"
        size="small"
        variant="outlined"
        sx={{ height: 24, fontSize: '0.6rem' }}
      />
    );
  }

  const { score, level, components } = scoreData;

  if (variant === 'compact') {
    return (
      <Tooltip
        title={
          <Box sx={{ p: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
              Öğrenme Seviyesi: {level} ({score}/100)
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', fontSize: '0.65rem' }}>
              📊 {components?.analysis_count?.label || 'Analiz yok'}
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', fontSize: '0.65rem' }}>
              ✅ {components?.verified_rules?.label || 'Kural yok'}
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', fontSize: '0.65rem' }}>
              📈 {components?.forecast_accuracy?.label || 'Forecast yok'}
            </Typography>
          </Box>
        }
        arrow
        placement="bottom"
      >
        <Chip
          icon={getLevelIcon(level)}
          label={`🧠 ${level} (${score})`}
          size="small"
          color={getLevelColor(level)}
          sx={{ height: 24, fontSize: '0.6rem', fontWeight: 600 }}
        />
      </Tooltip>
    );
  }

  return (
    <Paper
      sx={{
        p: 2,
        bgcolor: '#f8faff',
        border: '1px solid #e8f0fe',
        borderRadius: 2,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
          <CircularProgress
            variant="determinate"
            value={score}
            size={56}
            thickness={4}
            sx={{
              color: score >= 70 ? '#2e7d32' : score >= 40 ? '#ed6c02' : '#d32f2f',
            }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '0.9rem' }}>
              {score}
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem' }}>
            Öğrenme Seviyesi
          </Typography>
          <Chip
            icon={getLevelIcon(level)}
            label={level}
            size="small"
            color={getLevelColor(level)}
            sx={{ height: 22, fontSize: '0.65rem', fontWeight: 600 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.6rem' }}>
            Toplam {score}/100 puan
          </Typography>
        </Box>
      </Box>

      {showDetails && components && (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
          {Object.entries(components).map(([key, comp]) => {
            if (!comp) return null;
            return (
              <Box
                key={key}
                sx={{
                  p: 0.75,
                  bgcolor: 'white',
                  borderRadius: 1,
                  border: '1px solid #f0f0f0',
                }}
              >
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'block' }}>
                  {comp.label || key}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ flex: 1 }}>
                    <Box
                      sx={{
                        height: 4,
                        bgcolor: '#e8f0fe',
                        borderRadius: 2,
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          height: '100%',
                          width: `${Math.min(100, (comp.score / comp.max) * 100)}%`,
                          bgcolor: comp.score / comp.max > 0.7 ? '#2e7d32' : comp.score / comp.max > 0.4 ? '#ed6c02' : '#d32f2f',
                          borderRadius: 2,
                          transition: 'width 0.5s',
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="caption" sx={{ fontSize: '0.5rem', fontWeight: 600, minWidth: 20 }}>
                    {comp.score}/{comp.max}
                  </Typography>
                </Box>
              </Box>
            );
          })}
        </Box>
      )}
    </Paper>
  );
}