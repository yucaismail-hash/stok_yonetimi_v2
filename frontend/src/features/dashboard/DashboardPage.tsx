import { useState } from 'react';
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
import { useNavigate } from 'react-router-dom';

import ImportWizard from '../../components/ImportWizard';
import { useAuth } from '../../hooks/useAuth';
import { useCurrentPilotDataset } from '../dataset/api/pilotDatasetQueries';
import { useBusinessWorkflowReadiness } from '../business-workflow/api';
import { ROUTES } from '../../constants/routes';

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
  const navigate = useNavigate();
  const { user } = useAuth();
  const currentDataset = useCurrentPilotDataset(user?.company_id);
  const readiness = useBusinessWorkflowReadiness('LATEST_UPLOAD', Boolean(currentDataset.data));
  const allActiveReadiness = useBusinessWorkflowReadiness('ALL_ACTIVE_SKUS', Boolean(currentDataset.data));
  const [wizardOpen, setWizardOpen] = useState(false);

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

          {readiness.data?.coverage && <Card variant="outlined"><CardContent><Stack spacing={1}>
            <Typography component="h2" variant="h6">Veri Durumu</Typography>
            <Typography variant="body2" color="text.secondary">Kalıcı aktif SKU: {allActiveReadiness.data?.coverage?.total_scope_count ?? '—'} · Son yükleme SKU: {readiness.data.coverage.latest_upload_count} · Analiz edilebilir: {readiness.data.coverage.fully_analyzed_count} · Kısmi/uyarı: {readiness.data.coverage.partially_analyzed_count} · Hariç: {readiness.data.coverage.excluded_count}</Typography>
            <Button size="small" onClick={() => navigate(ROUTES.DATA_MANAGEMENT)} sx={{ alignSelf: 'flex-start' }}>Veri Yönetimini Aç</Button>
          </Stack></CardContent></Card>}

          <Card variant="outlined"><CardContent><Stack spacing={1} sx={{ alignItems: 'flex-start' }}>
            <Typography component="h2" variant="h6">Bütünleşik işletme analizi</Typography>
            <Typography id="business-workflow-help" variant="body2" color="text.secondary">
              Tahmin, stok, tedarikçi uygunluğu, simülasyon, geçmiş performans ve karar çıktıları tek bir işletme analizi akışında hazırlanır.
            </Typography>
            <Button variant="contained" onClick={() => navigate(ROUTES.BUSINESS_ANALYSIS)} aria-describedby="business-workflow-help">
              İşletme Analizini Başlat
            </Button>
          </Stack></CardContent></Card>
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
