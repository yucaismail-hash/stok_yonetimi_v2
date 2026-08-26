import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Paper,
  Skeleton,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from '@mui/material';
import { CheckCircle, CloudUpload, Dataset } from '@mui/icons-material';

import ImportWizard from '../../components/ImportWizard';
import { useAuth } from '../../hooks/useAuth';
import { useCurrentPilotDataset } from '../dataset/api/pilotDatasetQueries';
import {
  BusinessWorkflowApiError,
  BusinessWorkflowTracking,
  useStartBusinessWorkflow,
} from '../business-workflow';

const onboardingSteps = ['Excel dosyanızı yükleyin', 'Veriyi doğrulayın', 'Veri setini kabul edin'];

function DashboardLoading() {
  return (
    <Grid container spacing={2} aria-live="polite" aria-label="Veri seti yükleniyor">
      {[0, 1, 2, 3].map((item) => (
        <Grid key={item} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card variant="outlined">
            <CardContent>
              <Skeleton width="45%" />
              <Skeleton width="70%" height={42} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="text.secondary" variant="body2" gutterBottom>
          {label}
        </Typography>
        <Typography variant="h6" sx={{ overflowWrap: 'anywhere' }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const currentDataset = useCurrentPilotDataset(user?.company_id);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [executionId, setExecutionId] = useState<string | undefined>();
  const [duplicateExecution, setDuplicateExecution] = useState(false);
  const startWorkflow = useStartBusinessWorkflow();
  const executionMarkerKey = user?.company_id
    ? `stokonomi:business-workflow:active-execution:${user.company_id}`
    : undefined;

  useEffect(() => {
    setExecutionId(executionMarkerKey ? window.localStorage.getItem(executionMarkerKey) || undefined : undefined);
    setDuplicateExecution(false);
  }, [executionMarkerKey]);

  const clearUnavailableExecution = useCallback(() => {
    if (executionMarkerKey) window.localStorage.removeItem(executionMarkerKey);
    setExecutionId(undefined);
    setDuplicateExecution(false);
  }, [executionMarkerKey]);

  const startBusinessWorkflow = () => {
    startWorkflow.mutate(undefined, {
      onSuccess: (response) => {
        if (executionMarkerKey) window.localStorage.setItem(executionMarkerKey, response.execution_id);
        setDuplicateExecution(response.duplicate);
        setExecutionId(response.execution_id);
      },
    });
  };

  const displayName = user?.full_name?.trim() || user?.email || 'Kullanıcı';

  return (
    <Box sx={{ width: '100%', maxWidth: 1280, mx: 'auto' }}>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        sx={{ mb: 3, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' } }}
        spacing={1}
      >
        <Box>
          <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>
            Hoş geldiniz, {displayName}
          </Typography>
          <Typography color="text.secondary">Stokonomi çalışma alanınız</Typography>
        </Box>
        {Boolean(user?.role) && <Chip label={user?.role} variant="outlined" />}
      </Stack>

      {currentDataset.isPending && <DashboardLoading />}

      {currentDataset.isError && (
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={() => currentDataset.refetch()}>
              Tekrar dene
            </Button>
          }
        >
          Veri seti bilgisi alınamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin.
        </Alert>
      )}

      {currentDataset.isSuccess && currentDataset.data === null && (
        <Paper variant="outlined" sx={{ p: { xs: 2, sm: 4 } }}>
          <Stack spacing={3} sx={{ alignItems: 'center', textAlign: 'center' }}>
            <Dataset color="primary" sx={{ fontSize: 48 }} aria-hidden="true" />
            <Box>
              <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }} gutterBottom>
                İlk veri setinizi hazırlayın
              </Typography>
              <Typography color="text.secondary">
                Analize hazır bir çalışma alanı oluşturmak için Excel dosyanızı yükleyin ve doğrulayın.
              </Typography>
            </Box>
            <Stepper activeStep={0} alternativeLabel sx={{ width: '100%', maxWidth: 720 }}>
              {onboardingSteps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
            <Button variant="contained" startIcon={<CloudUpload />} onClick={() => setWizardOpen(true)}>
              Excel dosyası yükle
            </Button>
          </Stack>
        </Paper>
      )}

      {currentDataset.isSuccess && currentDataset.data !== null && (
        <Stack spacing={3}>
          <Alert severity="success" icon={<CheckCircle fontSize="inherit" />}>
            Veriniz analiz için hazır.
          </Alert>
          <Box>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 700 }} gutterBottom>
              Aktif veri seti
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <SummaryCard label="Kaynak" value={currentDataset.data.source_name || 'Kaynak adı belirtilmemiş'} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <SummaryCard label="Kayıt sayısı" value={currentDataset.data.record_count.toLocaleString('tr-TR')} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <SummaryCard label="Malzeme sayısı" value={currentDataset.data.material_count.toLocaleString('tr-TR')} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <SummaryCard
                  label="Kabul tarihi"
                  value={new Intl.DateTimeFormat('tr-TR', { dateStyle: 'medium', timeStyle: 'short' }).format(
                    new Date(currentDataset.data.accepted_at),
                  )}
                />
              </Grid>
            </Grid>
          </Box>
          <Chip label="Analize Hazır" color="success" sx={{ alignSelf: 'flex-start' }} />

          {executionId ? (
            <Stack spacing={1}>
              {duplicateExecution && <Alert severity="info">Devam eden analiz bulundu; mevcut çalışmayı gösteriyoruz.</Alert>}
              <Button
                variant="outlined"
                onClick={() => document.getElementById('business-workflow-tracking')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                sx={{ alignSelf: 'flex-start' }}
              >
                Devam Eden Analizi Gör
              </Button>
              {startWorkflow.isError && (
                <Alert severity="warning">
                  Analiz yeniden başlatılamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin.
                </Alert>
              )}
              <BusinessWorkflowTracking
                executionId={executionId}
                onUnavailable={clearUnavailableExecution}
                onStartAgain={startBusinessWorkflow}
              />
            </Stack>
          ) : (
            <Stack spacing={1} sx={{ alignItems: 'flex-start' }}>
              <Button
                variant="contained"
                onClick={startBusinessWorkflow}
                disabled={startWorkflow.isPending}
                aria-describedby="business-workflow-help"
              >
                {startWorkflow.isPending ? 'Analiz başlatılıyor…' : 'Analizi Başlat'}
              </Button>
              <Typography id="business-workflow-help" variant="body2" color="text.secondary">
                Hazır veri setiniz için tüm business workflow analizleri sıraya alınır.
              </Typography>
              {startWorkflow.isError && (
                <Alert severity="warning">
                  {startWorkflow.error instanceof BusinessWorkflowApiError && startWorkflow.error.kind === 'dataset-unavailable'
                    ? 'Veri setiniz henüz analiz için hazır değil.'
                    : startWorkflow.error instanceof BusinessWorkflowApiError && startWorkflow.error.kind === 'service-unavailable'
                      ? 'Analiz kuyruğu geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.'
                      : startWorkflow.error instanceof BusinessWorkflowApiError && startWorkflow.error.kind === 'unauthorized'
                        ? 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.'
                        : 'Analiz başlatılamadı. Bağlantınızı kontrol edip tekrar deneyin.'}
                </Alert>
              )}
            </Stack>
          )}
        </Stack>
      )}

      <ImportWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onComplete={() => setWizardOpen(false)}
      />
    </Box>
  );
}
