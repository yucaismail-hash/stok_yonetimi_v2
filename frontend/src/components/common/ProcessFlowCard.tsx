// frontend/src/components/common/ProcessFlowCard.tsx
// Stokonomi Design System - Process Flow (Reusable)

import { Box, Typography, Stepper, Step, StepLabel, Paper, CircularProgress, Chip } from '@mui/material';
import { CheckCircle, Error, Pending, PlayArrow } from '@mui/icons-material';

export interface ProcessStep {
  label: string;
  description?: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  timestamp?: string;
}

interface ProcessFlowCardProps {
  steps: ProcessStep[];
  activeStep: number;
  isComplete: boolean;
  title?: string;
  compact?: boolean;
  progress?: number;
  progressLabel?: string;
}

export default function ProcessFlowCard({
  steps,
  activeStep,
  isComplete,
  title = 'İşlem Akışı',
  compact = false,
  progress,
  progressLabel,
}: ProcessFlowCardProps) {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'error':
        return <Error color="error" fontSize="small" />;
      case 'completed':
        return <CheckCircle color="success" fontSize="small" />;
      case 'active':
        return <CircularProgress size={14} />;
      default:
        return <Pending color="disabled" fontSize="small" />;
    }
  };

  return (
    <Paper
      sx={{
        p: compact ? 1.25 : 1.5,
        borderRadius: 2,
        border: '1px solid #e8f0fe',
        bgcolor: '#fafcff',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: compact ? 0.5 : 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayArrow sx={{ fontSize: 18, color: '#1f4e79' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1f4e79', fontSize: compact ? '0.7rem' : '0.75rem' }}>
            {title}
          </Typography>
          {isComplete && (
            <Chip
              label="✅ Tamamlandı"
              size="small"
              color="success"
              sx={{ height: 18, fontSize: '0.5rem' }}
            />
          )}
        </Box>
        {progress !== undefined && (
          <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#6b7280' }}>
            {progressLabel || '%' + progress}
          </Typography>
        )}
      </Box>

      <Stepper
        activeStep={activeStep}
        orientation="vertical"
        sx={{
          '& .MuiStepConnector-line': { display: 'none' },
          '& .MuiStep-root': {
            padding: compact ? '1px 0' : '2px 0',
          },
        }}
      >
        {steps.map((step, index) => {
          const isActive = index === activeStep;
          const isCompleted = index < activeStep || (isComplete && index === activeStep);
          const isError = step.status === 'error';

          return (
            <Step key={index} completed={isCompleted}>
              <StepLabel
                icon={getStepIcon(step.status)}
                sx={{
                  '& .MuiStepLabel-label': {
                    color: isError ? '#d32f2f' : isActive ? '#1f4e79' : isCompleted ? '#2e7d32' : '#9e9e9e',
                    fontWeight: isActive ? 600 : 400,
                    fontSize: compact ? '0.65rem' : '0.7rem',
                  },
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                  <Typography variant="body2" sx={{ fontWeight: isActive ? 600 : 400, fontSize: compact ? '0.65rem' : '0.7rem' }}>
                    {step.label}
                  </Typography>
                  {step.timestamp && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.5rem' }}>
                      {step.timestamp}
                    </Typography>
                  )}
                </Box>
                {!compact && step.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.55rem' }}>
                    {step.description}
                  </Typography>
                )}
              </StepLabel>
            </Step>
          );
        })}
      </Stepper>

      {progress !== undefined && (
        <Box sx={{ mt: 1 }}>
          <Box
            sx={{
              height: 3,
              bgcolor: '#e8f0fe',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                height: '100%',
                width: `${progress}%`,
                bgcolor: progress === 100 ? '#2e7d32' : '#1f4e79',
                borderRadius: 2,
                transition: 'width 0.5s',
              }}
            />
          </Box>
        </Box>
      )}
    </Paper>
  );
}