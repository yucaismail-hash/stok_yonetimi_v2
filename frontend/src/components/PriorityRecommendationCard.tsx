// frontend/src/components/PriorityRecommendationCard.tsx

import { Card, CardContent, Box, Typography, Button, Chip, Avatar } from '@mui/material';
import { Lightbulb, ArrowForward } from '@mui/icons-material';

import { Recommendation } from '../types/recommendation';


interface Props {
  recommendation: Recommendation;
  loading: boolean;
  onAction: (rec: Recommendation) => void;
}

export const PriorityRecommendationCard = ({ recommendation, loading, onAction }: Props) => {
  if (loading || !recommendation) return null;

  const priorityColors: Record<number, string> = {
    100: '#d32f2f',
    90: '#ed6c02',
    80: '#ed6c02',
    70: '#1976d2',
    60: '#2e7d32',
    50: '#6b7280',
  };

  const color = priorityColors[recommendation.priority] || '#1976d2';

  return (
    <Card sx={{
      borderRadius: 3,
      border: `1px solid ${color}20`,
      bgcolor: `${color}08`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, bgcolor: color }} />
      
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Avatar sx={{ bgcolor: `${color}15`, color: color, width: 40, height: 40 }}>
            <Lightbulb sx={{ fontSize: 20 }} />
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: color, fontSize: '0.75rem', letterSpacing: '0.3px' }}>
                ⭐ AI Öncelikli Öneri
              </Typography>
              <Chip
                label={`Öncelik ${recommendation.priority}`}
                size="small"
                sx={{ height: 18, fontSize: '0.5rem', bgcolor: `${color}15`, color: color, fontWeight: 600 }}
              />
            </Box>
            
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79', fontSize: '1rem', mb: 0.5 }}>
              {recommendation.title}
            </Typography>
            
            <Typography variant="body2" sx={{ color: '#374151', fontSize: '0.85rem', mb: 0.5 }}>
              {recommendation.reason}
            </Typography>
            
            <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.7rem', display: 'block', mb: 1.5 }}>
              💡 {recommendation.benefit}
            </Typography>
            
            <Button
              variant="contained"
              endIcon={<ArrowForward />}
              onClick={() => onAction(recommendation)}
              sx={{
                bgcolor: color,
                '&:hover': { bgcolor: color, opacity: 0.85 },
                borderRadius: 2,
                textTransform: 'none',
                fontSize: '0.8rem',
                px: 3,
              }}
            >
              {recommendation.action_label || 'Başlat'}
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};