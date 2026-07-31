// frontend/src/components/common/AIAssistantCard.tsx
// 🤖 Stokonomi AI Analizi - Veritabanındaki ai_summary alanından gelir

import { Box, Typography, Paper, Chip, Avatar } from '@mui/material';
import { Psychology, CheckCircle } from '@mui/icons-material';

export interface AIAssistantData {
  summary: string;
  overall_risk?: string;
  confidence?: number;
  recommendations?: string[];
  topMethod?: string;
  kpis?: {
    total_items?: number;
    high_risk_count?: number;
    increase_count?: number;
    decrease_count?: number;
    maintain_count?: number;
  };
  version?: string;
  generatedAt?: string;
}

export interface AIAssistantCardProps {
  data?: AIAssistantData | null;
  loading?: boolean;
  compact?: boolean;
  version?: string;
  generatedAt?: string;
}

export default function AIAssistantCard({
  data,
  loading = false,
  compact = false,
  version = 'Stokonomi AI v1.0',
  generatedAt,
}: AIAssistantCardProps) {
  const displayVersion = data?.version || version;
  const displayGeneratedAt = data?.generatedAt || generatedAt || new Date().toLocaleString('tr-TR');

  if (loading) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#f8faff', minHeight: 80 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ bgcolor: '#1f4e79', width: 32, height: 32 }}>
            <Psychology sx={{ fontSize: 16, color: 'white' }} />
          </Avatar>
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.75rem' }}>
            🤖 Stokonomi AI Analizi yükleniyor...
          </Typography>
        </Box>
      </Paper>
    );
  }

  if (!data || !data.summary) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px dashed #d0d0d0', bgcolor: '#fafafa', minHeight: 80 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar sx={{ bgcolor: '#e0e0e0', width: 32, height: 32 }}>
            <Psychology sx={{ fontSize: 16, color: '#9e9e9e' }} />
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#6b7280', fontSize: '0.75rem' }}>
              🤖 Stokonomi AI Analizi
            </Typography>
            <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
              Henüz AI özeti oluşturulmamış. Analiz tamamlandığında burada görünecek.
            </Typography>
          </Box>
        </Box>
      </Paper>
    );
  }

  const { summary, overall_risk, confidence, recommendations, topMethod, kpis } = data;

  const getRiskChipColor = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case 'yüksek':
      case 'high':
        return 'error';
      case 'orta':
      case 'medium':
        return 'warning';
      case 'düşük':
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <Paper
      sx={{
        p: compact ? 1.5 : 2,
        borderRadius: 2,
        border: '1px solid #d0e0ff',
        bgcolor: '#f0f7ff',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Üst çizgi */}
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: '#1f4e79' }} />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <Avatar sx={{ bgcolor: '#1f4e79', width: 36, height: 36 }}>
          <Psychology sx={{ fontSize: 18, color: 'white' }} />
        </Avatar>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 0.5 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.8rem' }}>
              🤖 Stokonomi AI Analizi
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '0.5rem', color: '#6b7280' }}>
              <Typography variant="caption" sx={{ fontSize: '0.45rem', lineHeight: 1.2, color: '#6b7280' }}>
                AI tarafından oluşturuldu
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.45rem', lineHeight: 1.2, fontWeight: 500, color: '#1f4e79' }}>
                {displayVersion} • {displayGeneratedAt}
              </Typography>
            </Box>
          </Box>

          {/* Risk ve Güven Chip'leri */}
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.25, flexWrap: 'wrap' }}>
            {overall_risk && (
              <Chip
                label={`Risk: ${overall_risk}`}
                size="small"
                color={getRiskChipColor(overall_risk)}
                sx={{ height: 18, fontSize: '0.5rem' }}
              />
            )}
            {confidence && (
              <Chip
                label={`Tahmin Güvenirliği %${Math.round(confidence * 100)}`}
                size="small"
                sx={{ height: 18, fontSize: '0.5rem', bgcolor: '#e8f0fe', color: '#1f4e79' }}
              />
            )}
          </Box>

          {/* Ana Özet Metni */}
          <Typography
            variant="body2"
            sx={{
              color: '#374151',
              fontSize: compact ? '0.75rem' : '0.85rem',
              lineHeight: 1.6,
              mt: 0.5,
              p: 1.5,
              bgcolor: 'rgba(255,255,255,0.7)',
              borderRadius: 1,
              border: '1px solid #d0e0ff',
            }}
          >
            {summary}
          </Typography>

          {/* Öneriler */}
          {recommendations && recommendations.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', fontWeight: 600 }}>
                💡 Öneriler
              </Typography>
              <Box sx={{ mt: 0.25 }}>
                {recommendations.slice(0, 3).map((rec, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                      p: 0.25,
                      fontSize: '0.65rem',
                      color: '#374151',
                    }}
                  >
                    <CheckCircle sx={{ fontSize: 12, color: '#1f4e79' }} />
                    {rec}
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {/* KPI'lar + En İyi Metot */}
          <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {kpis?.total_items !== undefined && kpis.total_items > 0 && (
              <Chip 
                label={`📦 ${kpis.total_items} Ürün analiz edildi`} 
                size="small" 
                variant="outlined" 
                sx={{ height: 20, fontSize: '0.5rem' }} 
              />
            )}
            {kpis?.increase_count !== undefined && kpis.increase_count > 0 && (
              <Chip 
                label={`📈 ${kpis.increase_count} Ürünün EM stokunu artır`} 
                size="small" 
                color="error" 
                variant="outlined" 
                sx={{ height: 20, fontSize: '0.5rem' }} 
              />
            )}
            {kpis?.decrease_count !== undefined && kpis.decrease_count > 0 && (
              <Chip 
                label={`📉 ${kpis.decrease_count} Ürünün EM stokunu azalt`} 
                size="small" 
                color="success" 
                variant="outlined" 
                sx={{ height: 20, fontSize: '0.5rem' }} 
              />
            )}
            {kpis?.maintain_count !== undefined && kpis.maintain_count > 0 && (
              <Chip 
                label={`✅ ${kpis.maintain_count} Ürünün EM stokunu koru`} 
                size="small" 
                color="info" 
                variant="outlined" 
                sx={{ height: 20, fontSize: '0.5rem' }} 
              />
            )}
            {kpis?.high_risk_count !== undefined && kpis.high_risk_count > 0 && (
              <Chip 
                label={`⚠️ ${kpis.high_risk_count} Ürün yüksek riskli`} 
                size="small" 
                color="warning" 
                variant="outlined" 
                sx={{ height: 20, fontSize: '0.5rem' }} 
              />
            )}
            {topMethod && (
              <Chip
                label={`En Çok ⭐ (${topMethod}) Metodu Kullanıldı`}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.5rem',
                  bgcolor: '#fff3e0',
                  color: '#e65100',
                  border: '1px solid #ffcc80',
                  fontWeight: 600,
                }}
              />
            )}
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}