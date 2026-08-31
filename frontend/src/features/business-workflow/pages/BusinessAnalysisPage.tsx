import { Alert, Box, Button, Card, CardContent, Chip, Grid, MenuItem, Paper, Select, Stack, Step, StepLabel, Stepper, Typography } from '@mui/material';
import { useState } from 'react';
import { CheckCircle, PlayArrow } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { ROUTES } from '../../../constants/routes';
import { useAuth } from '../../../hooks/useAuth';
import { useCurrentPilotDataset } from '../../dataset/api/pilotDatasetQueries';
import { BusinessWorkflowApiError, type BusinessWorkflowScopeMode, useBusinessWorkflowReadiness } from '../api';
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

const capabilityLabels: Record<string, string> = {
  forecast: 'Talep Tahmini', safety_stock: 'Emniyet Stoku', supplier: 'Tedarikçi Analizi',
  simulation: 'Simülasyon', backtest: 'Geçmiş Performans Testi', decision_intelligence: 'Karar Zekâsı',
};

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
  const [scopeMode, setScopeMode] = useState<BusinessWorkflowScopeMode>('LATEST_UPLOAD');
  const readiness = useBusinessWorkflowReadiness(scopeMode, Boolean(dataset.data));
  const workflowBlocked = readiness.data?.status === 'BLOCKED';
  const coverage = readiness.data?.coverage;

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
            <Alert severity={workflowBlocked ? 'warning' : readiness.data?.status === 'READY_WITH_EXCLUSIONS' ? 'info' : 'success'} icon={<CheckCircle fontSize="inherit" />}>
              {workflowBlocked ? 'Veri seti zorunlu iş akışı için henüz yeterli değil.' : readiness.data?.status === 'READY_WITH_EXCLUSIONS' ? 'İşletme analizi uygun ürünlerde yürütülecek; kapsam dışı ürünler raporlanacak.' : 'Veri setiniz işletme analizi için hazır.'}
            </Alert>
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

            {coverage && <Card variant="outlined"><CardContent><Stack spacing={1.25}>
              <Typography component="h2" variant="h6">Analiz Kapsamı</Typography>
              <Grid container spacing={1}>
                <Grid size={{ xs: 6, md: 3 }}><SummaryCard label="Toplam ürün" value={coverage.total_scope_count.toLocaleString('tr-TR')} /></Grid>
                <Grid size={{ xs: 6, md: 3 }}><SummaryCard label="Tam analiz" value={coverage.fully_analyzed_count.toLocaleString('tr-TR')} /></Grid>
                <Grid size={{ xs: 6, md: 3 }}><SummaryCard label="Kısmi analiz" value={coverage.partially_analyzed_count.toLocaleString('tr-TR')} /></Grid>
                <Grid size={{ xs: 6, md: 3 }}><SummaryCard label="Analiz edilmeyen" value={coverage.excluded_count.toLocaleString('tr-TR')} /></Grid>
              </Grid>
              {coverage.exclusions.map((item, index) => <Paper key={`${item.material_code}-${item.capability}-${index}`} variant="outlined" sx={{ p: 1.25 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{item.product_name || item.material_code} · {capabilityLabels[item.capability] || item.capability}</Typography>
                <Typography variant="body2" color="text.secondary">{item.message}</Typography>
              </Paper>)}
            </Stack></CardContent></Card>}

            <Card variant="outlined">
              <CardContent><Stack spacing={1.25}>
                <Typography component="h2" variant="h6">Veri Uygunluk Kontrolü</Typography>
                <Stack spacing={0.5} sx={{ maxWidth: 620 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>Analiz kapsamı</Typography>
                  <Select size="small" value={scopeMode} onChange={(event) => setScopeMode(event.target.value as BusinessWorkflowScopeMode)} inputProps={{ 'aria-label': 'Analiz kapsamı' }}>
                    <MenuItem value="LATEST_UPLOAD">Yalnızca son yüklemedeki SKU'ları analiz et</MenuItem>
                    <MenuItem value="ALL_ACTIVE_SKUS">Sistemde kayıtlı tüm aktif SKU'ları analiz et</MenuItem>
                  </Select>
                  {scopeMode === 'ALL_ACTIVE_SKUS' && <Alert severity="warning">Son yüklemede bulunmayan SKU’larda geçmiş ve etkili master veriler kullanılabilir; güncel stok, açık sipariş ve planlanan teslim verisi taşınmaz. Sonuç kalitesi etkilenebilir.</Alert>}
                </Stack>
                {readiness.isPending && <Typography role="status" color="text.secondary">İşletme analizi uygunluğu kontrol ediliyor…</Typography>}
                {readiness.isError && <Alert severity="warning" action={<Button color="inherit" onClick={() => readiness.refetch()}>Tekrar dene</Button>}>İşletme analizi uygunluğu şu anda doğrulanamadı. Başlatma sınırı sunucuda korunur.</Alert>}
                {readiness.data?.capabilities.map((capability) => (
                  <Stack key={capability.capability} direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' }, borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{capabilityLabels[capability.capability] || capability.capability}</Typography>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Chip size="small" color={capability.status === 'READY' ? 'success' : capability.status === 'BLOCKED' ? 'error' : 'default'} label={capability.status === 'READY' ? 'Çalıştırılabilir' : capability.status === 'OPTIONAL_UNAVAILABLE' ? 'Uygulanmayacak' : 'Engellendi'} />
                      {capability.message && <Typography variant="body2" color="text.secondary">{capability.message}</Typography>}
                    </Stack>
                  </Stack>
                ))}
              </Stack></CardContent>
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
                <Button variant="contained" startIcon={<PlayArrow />} onClick={() => entry.startBusinessWorkflow(scopeMode)} disabled={entry.startWorkflow.isPending || workflowBlocked || readiness.isPending}>
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
