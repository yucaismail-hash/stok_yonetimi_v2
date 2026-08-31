import { Alert, Box, Button, Card, CardContent, Chip, Grid, Paper, Stack, Step, StepLabel, Stepper, Typography } from '@mui/material';
import { CheckCircle, PlayArrow } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { ROUTES } from '../../../constants/routes';
import { useAuth } from '../../../hooks/useAuth';
import { useCurrentPilotDataset } from '../../dataset/api/pilotDatasetQueries';
import { BusinessWorkflowApiError } from '../api';
import { BusinessWorkflowTracking } from '../components/BusinessWorkflowTracking';
import { useBusinessWorkflowEntry } from '../useBusinessWorkflowEntry';

const workflowSteps = [
  'Talep Tahmini',
  'Emniyet Stoku',
  'Tedarikçi (uygunsa)',
  'Simülasyon',
  'Geçmiş Performans Testi',
  'Karar Zekâsı',
];

function SummaryCard({ label, value }: { label: string; value: string }) {
  return <Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">{label}</Typography><Typography variant="h6">{value}</Typography></CardContent></Card>;
}

function startErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'İşletme analizi başlatılamadı. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'dataset-unavailable') return 'Veri setiniz henüz işletme analizi için hazır değil.';
  if (error.kind === 'service-unavailable') return 'Analiz kuyruğu geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  return 'İşletme analizi şu anda başlatılamadı. Lütfen daha sonra tekrar deneyin.';
}

export default function BusinessAnalysisPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const dataset = useCurrentPilotDataset(user?.company_id);
  const entry = useBusinessWorkflowEntry(user?.company_id);

  return (
    <Box sx={{ width: '100%', maxWidth: 1280, mx: 'auto' }}>
      <Stack spacing={3}>
        <Box>
          <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>İşletme Analizi</Typography>
          <Typography color="text.secondary">Tek bir akışta tahmin, stok, risk ve karar çıktılarını hazırlayın.</Typography>
        </Box>

        {dataset.isPending && <Paper variant="outlined" sx={{ p: 3 }}><Typography role="status">Aktif veri seti yükleniyor…</Typography></Paper>}
        {dataset.isError && <Alert severity="error" action={<Button color="inherit" onClick={() => dataset.refetch()}>Tekrar dene</Button>}>Aktif veri seti bilgisi alınamadı.</Alert>}
        {dataset.isSuccess && dataset.data === null && (
          <Alert severity="info" action={<Button color="inherit" onClick={() => navigate(ROUTES.DASHBOARD)}>Veri setine git</Button>}>
            İşletme analizi için önce bir veri setini kabul edin.
          </Alert>
        )}

        {dataset.data && (
          <>
            <Alert severity="success" icon={<CheckCircle fontSize="inherit" />}>Veri setiniz işletme analizi için hazır.</Alert>
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Typography component="h2" variant="h6">Aktif veri seti</Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 4 }}><SummaryCard label="Kayıt sayısı" value={dataset.data.record_count.toLocaleString('tr-TR')} /></Grid>
                    <Grid size={{ xs: 12, sm: 4 }}><SummaryCard label="Ürün sayısı" value={dataset.data.material_count.toLocaleString('tr-TR')} /></Grid>
                    <Grid size={{ xs: 12, sm: 4 }}><SummaryCard label="Hazırlık durumu" value="Analize hazır" /></Grid>
                  </Grid>
                  <Typography variant="body2" color="text.secondary">Kaynak: {dataset.data.source_name || 'Kaynak adı belirtilmemiş'}</Typography>
                </Stack>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Box><Typography component="h2" variant="h6">Entegre analiz akışı</Typography><Typography color="text.secondary">Adımlar sırayla ve arka planda yürütülür; tedarikçi adımı uygun olduğunda eklenir.</Typography></Box>
                  <Stepper alternativeLabel activeStep={-1} sx={{ overflowX: 'auto', py: 1 }}>
                    {workflowSteps.map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
                  </Stepper>
                </Stack>
              </CardContent>
            </Card>

            {entry.executionId ? (
              <Stack spacing={1}>
                {entry.duplicateExecution && <Alert severity="info">Devam eden işletme analizi bulundu; mevcut çalışmayı gösteriyoruz.</Alert>}
                <BusinessWorkflowTracking executionId={entry.executionId} onUnavailable={entry.clearUnavailableExecution} onStartAgain={entry.startBusinessWorkflow} />
              </Stack>
            ) : (
              <Card variant="outlined"><CardContent><Stack spacing={1.5} sx={{ alignItems: 'flex-start' }}>
                <Typography component="h2" variant="h6">İşletme analizini başlatın</Typography>
                <Typography color="text.secondary">Aktif veri setiniz için bütünleşik analiz akışı güvenli biçimde sıraya alınır.</Typography>
                <Button variant="contained" startIcon={<PlayArrow />} onClick={entry.startBusinessWorkflow} disabled={entry.startWorkflow.isPending}>
                  {entry.startWorkflow.isPending ? 'İşletme analizi başlatılıyor…' : 'İşletme Analizini Başlat'}
                </Button>
                {entry.startWorkflow.isError && <Alert severity="warning">{startErrorMessage(entry.startWorkflow.error)}</Alert>}
              </Stack></CardContent></Card>
            )}
          </>
        )}
      </Stack>
    </Box>
  );
}
