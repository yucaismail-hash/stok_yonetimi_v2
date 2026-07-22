// frontend/src/components/AttentionRequiredSection.tsx

import { Card, CardContent, Box, Typography, Button, Chip, Paper, Stack } from '@mui/material';
import { Warning, ArrowForward } from '@mui/icons-material';
import { Recommendation } from '../types/recommendation';

interface Props {
  items: Recommendation[];
  loading: boolean;
  onAction: (rec: Recommendation) => void;
}

export const AttentionRequiredSection = ({ items, loading, onAction }: Props) => {
  if (loading || !items || items.length === 0) return null;

  return (
    <Card sx={{ borderRadius: 3, border: '1px solid #e8f0fe' }}>
      <CardContent sx={{ py: 2.5, px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Warning sx={{ fontSize: 20, color: '#ed6c02' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.85rem' }}>
            Dikkat Gerekenler
          </Typography>
          <Chip
            label={`${items.length}`}
            size="small"
            color="warning"
            sx={{ height: 20, fontSize: '0.55rem', fontWeight: 600 }}
          />
        </Box>

        <Stack spacing={1.5}>
          {items.map((item, idx) => (
            <Paper
              key={idx}
              sx={{
                p: 1.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: '#fafcff',
                border: '1px solid #ffecb3',
                borderRadius: 2,
                transition: 'all 0.2s',
                '&:hover': { bgcolor: '#fff8e1' },
              }}
            >
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: '0.8rem' }}>
                  {item.title}
                </Typography>
                <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.65rem', display: 'block' }}>
                  {item.reason}
                </Typography>
              </Box>
              <Button
                size="small"
                variant="contained"
                color="warning"
                onClick={() => onAction(item)}
                sx={{
                  fontSize: '0.6rem',
                  textTransform: 'none',
                  borderRadius: 2,
                  ml: 1,
                  flexShrink: 0,
                  px: 2,
                  py: 0.5,
                  minWidth: 70,
                }}
              >
                İncele
              </Button>
            </Paper>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};