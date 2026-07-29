// frontend/src/components/Dashboard/AIContextPanel.tsx
// AI İşletmenizi Tanıyor - Learning Engine'den öğrenilen davranışlar

import { Box, Typography, Paper, Chip, CircularProgress, Alert, Tooltip, Skeleton } from '@mui/material';
import { CheckCircle, Warning, Lightbulb, TrendingUp, Timeline, LocalShipping, AutoAwesome } from '@mui/icons-material';
import { useVerifiedRules } from '../../hooks/useCompanyMemory';
import { CompanyRule } from '../../hooks/useCompanyMemory';

interface AIContextPanelProps {
  maxItems?: number;
  title?: string;
}

const getRuleIcon = (ruleType: string) => {
  switch (ruleType) {
    case 'seasonal':
      return <Timeline sx={{ fontSize: 16 }} />;
    case 'intermittent':
      return <Warning sx={{ fontSize: 16 }} />;
    case 'lead_time':
      return <LocalShipping sx={{ fontSize: 16 }} />;
    case 'trend':
      return <TrendingUp sx={{ fontSize: 16 }} />;
    case 'supplier':
      return <LocalShipping sx={{ fontSize: 16 }} />;
    case 'successful_method':
      return <AutoAwesome sx={{ fontSize: 16 }} />;
    default:
      return <Lightbulb sx={{ fontSize: 16 }} />;
  }
};

const getConfidenceColor = (confidence: number): 'success' | 'warning' | 'error' | 'default' => {
  if (confidence >= 0.7) return 'success';
  if (confidence >= 0.4) return 'warning';
  return 'error';
};

export default function AIContextPanel({ maxItems = 8, title = '🧠 AI İşletmenizi Tanıyor' }: AIContextPanelProps) {
  const { data: rules, isLoading, isError } = useVerifiedRules();

  if (isLoading) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Lightbulb sx={{ fontSize: 20, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79' }}>
            {title}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={40} sx={{ borderRadius: 1.5 }} />
          ))}
        </Box>
      </Paper>
    );
  }

  if (isError) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Lightbulb sx={{ fontSize: 20, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79' }}>
            {title}
          </Typography>
        </Box>
        <Alert severity="error" sx={{ fontSize: '0.75rem' }}>
          Öğrenilen davranışlar yüklenemedi. Lütfen daha sonra tekrar deneyin.
        </Alert>
      </Paper>
    );
  }

  if (!rules || rules.length === 0) {
    return (
      <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Lightbulb sx={{ fontSize: 20, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79' }}>
            {title}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" sx={{ color: '#6b7280', fontSize: '0.8rem' }}>
            Henüz yeterli analiz verisi yok.
          </Typography>
          <Typography variant="caption" sx={{ color: '#9e9e9e', fontSize: '0.65rem' }}>
            Analiz yaptıkça AI işletmenizi tanımaya başlayacak.
          </Typography>
        </Box>
      </Paper>
    );
  }

  const displayRules = rules.slice(0, maxItems);

  return (
    <Paper sx={{ p: 2, borderRadius: 2, border: '1px solid #e8f0fe', bgcolor: '#fafcff' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <Lightbulb sx={{ fontSize: 20, color: '#1f4e79' }} />
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79' }}>
          {title}
        </Typography>
        <Chip
          label={`${rules.length} davranış`}
          size="small"
          sx={{ height: 18, fontSize: '0.5rem', bgcolor: '#e8f0fe' }}
        />
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        {displayRules.map((rule) => (
          <Tooltip
            key={rule.id}
            title={
              <Box sx={{ p: 1, maxWidth: 300 }}>
                <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 600, color: '#1f4e79', display: 'block' }}>
                  {rule.rule_name}
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#374151', display: 'block', mt: 0.25 }}>
                  {rule.description}
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', display: 'block', mt: 0.25 }}>
                  🔄 {rule.usage_count} kez kullanıldı
                </Typography>
              </Box>
            }
            arrow
            placement="top"
          >
            <Paper
              sx={{
                p: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'white',
                border: `1px solid ${rule.confidence_score >= 0.7 ? '#a5d6a7' : rule.confidence_score >= 0.4 ? '#ffcc80' : '#ef9a9a'}`,
                borderRadius: 1.5,
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 1,
                  bgcolor: '#f8faff',
                },
              }}
            >
              <Box sx={{ color: rule.confidence_score >= 0.7 ? '#2e7d32' : rule.confidence_score >= 0.4 ? '#ed6c02' : '#d32f2f' }}>
                {getRuleIcon(rule.rule_type)}
              </Box>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="body2" sx={{ fontSize: '0.7rem', fontWeight: 500, color: '#1f4e79' }}>
                  {rule.rule_name}
                </Typography>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {rule.description}
                </Typography>
              </Box>
              <Chip
                icon={<CheckCircle sx={{ fontSize: 12 }} />}
                label={`%${Math.round(rule.confidence_score * 100)}`}
                size="small"
                color={getConfidenceColor(rule.confidence_score)}
                sx={{ height: 18, fontSize: '0.5rem', fontWeight: 600, flexShrink: 0 }}
              />
            </Paper>
          </Tooltip>
        ))}
      </Box>

      {rules.length > maxItems && (
        <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'center', fontSize: '0.55rem', color: '#9e9e9e' }}>
          +{rules.length - maxItems} daha davranış
        </Typography>
      )}
    </Paper>
  );
}