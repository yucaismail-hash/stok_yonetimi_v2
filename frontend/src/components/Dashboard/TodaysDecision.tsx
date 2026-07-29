// frontend/src/components/Dashboard/TodaysDecision.tsx
// Bugünün Kararı - AI Decision Engine'den gelen karar

import { Box, Typography, Paper, Chip, Button, Avatar, Skeleton, alpha } from '@mui/material';
import { Lightbulb, ArrowForward, CheckCircle, Warning, Error as ErrorIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';

interface DecisionData {
  decision: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  reasons: string[];
  expected_impact: {
    stockout_risk?: string;
    inventory_cost?: string;
    [key: string]: string | undefined;
  };
  next_review_days: number;
  explanation: string;
  generated_at: string;
  analysis_type: string;
}

interface TodaysDecisionResponse {
  success: boolean;
  has_decision: boolean;
  decision: DecisionData | null;
  message?: string;
}

const priorityColors = {
  critical: { bg: '#ffebee', color: '#d32f2f', label: 'Kritik' },
  high: { bg: '#fff3e0', color: '#ed6c02', label: 'Yüksek' },
  medium: { bg: '#e3f2fd', color: '#1976d2', label: 'Orta' },
  low: { bg: '#e8f5e9', color: '#2e7d32', label: 'Düşük' },
};

const decisionLabels: Record<string, string> = {
  increase_safety_stock: '📦 Emniyet Stoğunu Artır',
  decrease_safety_stock: '📦 Emniyet Stoğunu Azalt',
  change_forecast_model: '📊 Tahmin Modelini Değiştir',
  review_supplier: '🔍 Tedarikçiyi Gözden Geçir',
  investigate_variability: '📈 Değişkenliği Araştır',
  seasonal_adjustment: '🌊 Mevsimsel Ayarlama Yap',
  maintain_current: '✅ Mevcut Durumu Koru',
  urgent_action: '🚨 Acil Aksiyon Al',
  normal_monitoring: '📋 Normal Takip'
};

export default function TodaysDecision() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['todays-decision'],
    queryFn: async (): Promise<TodaysDecisionResponse> => {
      try {
        const response = await api.get('/api/dashboard/todays-decision');
        return response.data;
      } catch (error) {
        console.error('❌ Bugünün kararı alınamadı:', error);
        return { success: false, has_decision: false, decision: null, message: 'Karar alınamadı' };
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#fafcff' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Skeleton variant="circular" width={40} height={40} />
          <Box sx={{ flex: 1 }}>
            <Skeleton variant="text" width="30%" height={16} />
            <Skeleton variant="text" width="60%" height={14} />
            <Skeleton variant="text" width="40%" height={14} />
          </Box>
        </Box>
      </Paper>
    );
  }

  if (isError || !data?.has_decision || !data?.decision) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#fafcff' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar sx={{ bgcolor: '#e0e0e0', width: 40, height: 40 }}>
            <Lightbulb sx={{ fontSize: 20, color: '#9e9e9e' }} />
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.75rem' }}>
              🎯 Bugünün Kararı
            </Typography>
            <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.8rem' }}>
              Henüz öneri oluşturulacak yeterli analiz verisi yok.
            </Typography>
            <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
              Bir analiz çalıştırarak başlayın.
            </Typography>
          </Box>
        </Box>
      </Paper>
    );
  }

  const decision = data.decision;
  const priority = priorityColors[decision.priority] || priorityColors.medium;
  const decisionLabel = decisionLabels[decision.decision] || decision.decision;

  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 2,
        border: `1px solid ${alpha(priority.color, 0.3)}`,
        bgcolor: alpha(priority.bg, 0.5),
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: priority.color }} />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <Avatar sx={{ bgcolor: alpha(priority.color, 0.15), color: priority.color, width: 40, height: 40 }}>
          <Lightbulb sx={{ fontSize: 20 }} />
        </Avatar>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.7rem', letterSpacing: '0.3px' }}>
              🎯 Bugünün Kararı
            </Typography>
            <Chip
              label={priority.label}
              size="small"
              sx={{
                height: 18,
                fontSize: '0.5rem',
                fontWeight: 600,
                bgcolor: priority.bg,
                color: priority.color,
              }}
            />
            <Chip
              label={`%${Math.round(decision.confidence * 100)} Güven`}
              size="small"
              variant="outlined"
              sx={{ height: 18, fontSize: '0.45rem' }}
            />
          </Box>

          <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.9rem', mb: 0.25 }}>
            {decisionLabel}
          </Typography>

          <Typography variant="body2" sx={{ color: '#374151', fontSize: '0.75rem', mb: 0.75, lineHeight: 1.5 }}>
            {decision.explanation}
          </Typography>

          {/* Sebepler */}
          {decision.reasons && decision.reasons.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 0.75 }}>
              {decision.reasons.slice(0, 4).map((reason, idx) => (
                <Chip
                  key={idx}
                  label={reason}
                  size="small"
                  variant="outlined"
                  sx={{ height: 18, fontSize: '0.5rem', borderColor: '#d0d0d0' }}
                />
              ))}
              {decision.reasons.length > 4 && (
                <Chip
                  label={`+${decision.reasons.length - 4}`}
                  size="small"
                  variant="outlined"
                  sx={{ height: 18, fontSize: '0.45rem' }}
                />
              )}
            </Box>
          )}

          {/* Beklenen Etki */}
          {decision.expected_impact && Object.keys(decision.expected_impact).length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mb: 0.75 }}>
              {Object.entries(decision.expected_impact).map(([key, value]) => {
                if (!value) return null;
                const isPositive = value.startsWith('-');
                return (
                  <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {isPositive ? (
                      <CheckCircle sx={{ fontSize: 14, color: '#2e7d32' }} />
                    ) : (
                      <Warning sx={{ fontSize: 14, color: '#ed6c02' }} />
                    )}
                    <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#374151' }}>
                      {key.replace('_', ' ')}: <strong style={{ color: isPositive ? '#2e7d32' : '#ed6c02' }}>{value}</strong>
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <Chip
              icon={<Lightbulb sx={{ fontSize: 12 }} />}
              label={`Sonraki inceleme: ${decision.next_review_days} gün`}
              size="small"
              variant="outlined"
              sx={{ height: 18, fontSize: '0.5rem' }}
            />
            <Button
              size="small"
              variant="contained"
              endIcon={<ArrowForward sx={{ fontSize: 14 }} />}
              sx={{
                bgcolor: priority.color,
                '&:hover': { bgcolor: priority.color, opacity: 0.85 },
                borderRadius: 2,
                textTransform: 'none',
                fontSize: '0.65rem',
                py: 0.25,
                px: 1.5,
                minHeight: 26,
              }}
              onClick={() => {
                const path = decision.analysis_type === 'safety_stock' ? '/safety-stock' :
                             decision.analysis_type === 'forecast' ? '/forecast' :
                             decision.analysis_type === 'simulation' ? '/simulation' :
                             decision.analysis_type === 'supplier' ? '/supplier' :
                             decision.analysis_type === 'backtest' ? '/backtest' : '/dashboard';
                window.location.href = path;
              }}
            >
              Analize Git
            </Button>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}