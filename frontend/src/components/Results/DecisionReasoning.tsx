// frontend/src/components/Results/DecisionReasoning.tsx
// AI Neden Bu Kararı Verdi? - Her kritik ürün için açıklama

import { Box, Typography, Paper, Chip, Divider, Tooltip, Grid, alpha } from '@mui/material';
import { CheckCircle, Warning, Error as ErrorIcon, Info, TrendingUp, TrendingDown } from '@mui/icons-material';

interface DecisionReasoningProps {
  materialCode: string;
  reasoning: {
    recommended_ss: number;
    current_ss?: number;
    reasons: string[];
    conclusion: string;
    confidence: number;
    factors: {
      cv: number;
      lead_time: number;
      intermittent: boolean;
      seasonal: boolean;
      risk_score: number;
      pattern: string;
    };
  };
}

const ReasonBadge = ({ reason }: { reason: string }) => {
  const getIcon = (text: string) => {
    if (text.includes('CV')) return <TrendingUp sx={{ fontSize: 12 }} />;
    if (text.includes('Lead Time')) return <Info sx={{ fontSize: 12 }} />;
    if (text.includes('Düzensiz')) return <Warning sx={{ fontSize: 12 }} />;
    if (text.includes('Yaz')) return <Info sx={{ fontSize: 12 }} />;
    if (text.includes('Risk')) return <ErrorIcon sx={{ fontSize: 12 }} />;
    return <CheckCircle sx={{ fontSize: 12 }} />;
  };

  const getColor = (text: string): 'error' | 'warning' | 'info' | 'success' | 'default' => {
    if (text.includes('CV') || text.includes('Risk') || text.includes('Düzensiz')) return 'error';
    if (text.includes('Lead Time')) return 'warning';
    if (text.includes('Yaz')) return 'info';
    return 'success';
  };

  return (
    <Chip
      icon={getIcon(reason)}
      label={reason}
      size="small"
      color={getColor(reason)}
      variant="outlined"
      sx={{
        height: 20,
        fontSize: '0.55rem',
        fontWeight: 500,
      }}
    />
  );
};

export default function DecisionReasoning({ materialCode, reasoning }: DecisionReasoningProps) {
  const { recommended_ss, current_ss, reasons, conclusion, confidence, factors } = reasoning;

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.7) return '#2e7d32';
    if (conf >= 0.4) return '#ed6c02';
    return '#d32f2f';
  };

  return (
    <Paper
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid #e8f0fe',
        bgcolor: '#fafcff',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '0.85rem' }}>
          📊 {materialCode} - Karar Analizi
        </Typography>
        <Chip
          label={`%${Math.round(confidence * 100)} Güven`}
          size="small"
          sx={{
            height: 20,
            fontSize: '0.55rem',
            fontWeight: 600,
            bgcolor: alpha(getConfidenceColor(confidence), 0.1),
            color: getConfidenceColor(confidence),
            border: `1px solid ${alpha(getConfidenceColor(confidence), 0.3)}`,
          }}
        />
      </Box>

      <Grid container spacing={1.5}>
        {/* SS Bilgisi */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{
              p: 1.5,
              bgcolor: '#f0f7ff',
              borderRadius: 1.5,
              border: '1px solid #d0e0ff',
            }}
          >
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block' }}>
              Önerilen Emniyet Stoğu
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1.5rem' }}>
              {recommended_ss}
            </Typography>
            {current_ss !== undefined && (
              <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block' }}>
                Mevcut: {current_ss} ({recommended_ss > current_ss ? `+${recommended_ss - current_ss}` : recommended_ss - current_ss})
              </Typography>
            )}
          </Box>
        </Grid>

        {/* Faktörler */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{
              p: 1.5,
              bgcolor: '#f5f5f5',
              borderRadius: 1.5,
              border: '1px solid #e8f0fe',
            }}
          >
            <Typography variant="caption" sx={{ fontSize: '0.55rem', color: '#6b7280', display: 'block', mb: 0.5 }}>
              Analiz Faktörleri
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0.5 }}>
              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'block' }}>CV</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: factors.cv > 0.7 ? '#d32f2f' : '#374151' }}>
                  {factors.cv.toFixed(3)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'block' }}>Lead Time</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: factors.lead_time > 21 ? '#d32f2f' : '#374151' }}>
                  {factors.lead_time} gün
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'block' }}>Risk Skoru</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: factors.risk_score > 0.5 ? '#d32f2f' : '#374151' }}>
                  {factors.risk_score.toFixed(2)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ fontSize: '0.5rem', color: '#9e9e9e', display: 'block' }}>Pattern</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.7rem', color: '#374151' }}>
                  {factors.pattern}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
              {factors.intermittent && (
                <Chip label="Aralıklı" size="small" color="warning" sx={{ height: 16, fontSize: '0.45rem' }} />
              )}
              {factors.seasonal && (
                <Chip label="Mevsimsel" size="small" color="info" sx={{ height: 16, fontSize: '0.45rem' }} />
              )}
            </Box>
          </Box>
        </Grid>
      </Grid>

      {/* Nedenler */}
      <Box sx={{ mt: 1.5 }}>
        <Typography variant="caption" sx={{ fontSize: '0.6rem', fontWeight: 600, color: '#1f4e79', display: 'block', mb: 0.5 }}>
          Neden?
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {reasons.map((reason, idx) => (
            <ReasonBadge key={idx} reason={reason} />
          ))}
        </Box>
      </Box>

      <Divider sx={{ my: 1 }} />

      {/* Sonuç */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CheckCircle sx={{ fontSize: 16, color: '#2e7d32' }} />
        <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.75rem', color: '#1f4e79' }}>
          Sonuç: {conclusion}
        </Typography>
      </Box>
    </Paper>
  );
}