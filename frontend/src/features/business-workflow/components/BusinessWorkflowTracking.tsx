import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Chip, LinearProgress, Stack, Typography } from '@mui/material';

import {
  BusinessWorkflowApiError,
  useExecution,
  useExecutionResult,
} from '../api';
import { executionStatusPresentation, presentWorkflowStage, safeFailureSummary } from '../executionPresentation';

function executionErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'Analiz durumu alınamadı. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'execution-unavailable') return 'Bu analiz kaydı artık kullanılamıyor.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  if (error.kind === 'service-unavailable') return 'Analiz servisi geçici olarak kullanılamıyor.';
  return 'Analiz durumu alınamadı. Lütfen daha sonra tekrar deneyin.';
}

export function BusinessWorkflowTracking({
  executionId,
  onUnavailable,
  onStartAgain,
}: {
  executionId: string;
  onUnavailable: () => void;
  onStartAgain: () => void;
}) {
  const execution = useExecution(executionId);
  const status = execution.data?.status;
  const result = useExecutionResult(executionId, status === 'completed');
  const [resultRequested, setResultRequested] = useState(false);

  useEffect(() => {
    if (execution.error instanceof BusinessWorkflowApiError && execution.error.kind === 'execution-unavailable') onUnavailable();
  }, [execution.error, onUnavailable]);

  if (execution.isPending) {
    return <Card variant="outlined"><CardContent><Typography role="status">Analiz durumu yükleniyor…</Typography></CardContent></Card>;
  }

  if (execution.isError) {
    return (
      <Alert severity="warning" action={<Button color="inherit" size="small" onClick={() => execution.refetch()}>Tekrar dene</Button>}>
        {executionErrorMessage(execution.error)}
      </Alert>
    );
  }

  const detail = execution.data;
  const progress = Math.max(0, Math.min(100, detail.progress));
  const isCompleted = detail.status === 'completed';
  const presentation = executionStatusPresentation[detail.status];
  const stage = presentWorkflowStage(detail.current_stage);
  const failureSummary = safeFailureSummary(detail.failure_summary);

  return (
    <Card id="business-workflow-tracking" variant="outlined" aria-live="polite">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' } }}>
            <Box>
              <Typography component="h2" variant="h6">{presentation.title}</Typography>
              <Typography role="status" color="text.secondary">{presentation.description}</Typography>
            </Box>
            <Chip label={detail.status} color={detail.status === 'failed' ? 'error' : detail.status === 'completed' ? 'success' : 'primary'} />
          </Stack>

          <Box>
            <LinearProgress variant="determinate" value={progress} aria-label={`Analiz ilerlemesi: yüzde ${progress}`} />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>İlerleme: %{progress}</Typography>
          </Box>

          {stage && <Typography variant="body2">Geçerli adım: {stage}</Typography>}
          {!presentation.terminal && (
            <Alert severity="info">
              Analiz arka planda devam eder. Bu sayfadan ayrılabilir; geri döndüğünüzde mevcut işlem yeniden yüklenir.
            </Alert>
          )}
          {detail.status === 'failed' && (
            <Alert severity="error" role="alert">
              {failureSummary ? `Destek referansı: ${failureSummary}` : 'İşlem tamamlanamadı. Lütfen daha sonra yeniden deneyin.'}
            </Alert>
          )}
          {detail.status === 'cancelled' && <Alert severity="info">Analiz iptal edildi.</Alert>}

          {isCompleted && result.isPending && <Typography role="status" variant="body2">Sonuç hazırlanıyor…</Typography>}
          {isCompleted && result.isSuccess && (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { sm: 'center' } }}>
              <Alert severity="success" sx={{ flex: 1 }}>Sonuç hazır.</Alert>
              <Button variant="outlined" onClick={() => setResultRequested(true)}>Sonuçları Gör</Button>
            </Stack>
          )}
          {resultRequested && result.isSuccess && <Typography variant="body2" color="text.secondary">Sonuç paketi hazır; ayrıntılı karar görünümü FU-F6 kapsamında sunulacak.</Typography>}
          {isCompleted && result.isError && (
            <Alert severity="warning" action={<Button color="inherit" size="small" onClick={() => result.refetch()}>Tekrar dene</Button>}>
              Sonuç şu anda görüntülenemiyor.
            </Alert>
          )}
          {(detail.status === 'failed' || detail.status === 'cancelled') && (
            <Button variant="outlined" onClick={onStartAgain}>Yeni Analizi Başlat</Button>
          )}
          <Typography variant="caption" color="text.secondary">Destek referansı: {detail.execution_id}</Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
