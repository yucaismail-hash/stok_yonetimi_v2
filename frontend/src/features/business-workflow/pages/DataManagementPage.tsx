import { Alert, Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';

import { useAuth } from '../../../hooks/useAuth';
import { useCurrentPilotDataset } from '../../dataset/api/pilotDatasetQueries';
import { useBusinessWorkflowReadiness } from '../api';

function Metric({ label, value }: { label: string; value: number | string }) {
  return <Card variant="outlined"><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h6">{value}</Typography></CardContent></Card>;
}

/** Read-only data management view; edits stay within the versioned import boundary. */
export default function DataManagementPage() {
  const { user } = useAuth();
  const dataset = useCurrentPilotDataset(user?.company_id);
  const readiness = useBusinessWorkflowReadiness('ALL_ACTIVE_SKUS', Boolean(dataset.data));
  const coverage = readiness.data?.coverage;
  return <Box sx={{ width: '100%', maxWidth: 1280, mx: 'auto' }}><Stack spacing={3}>
    <Box><Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>Veri Yönetimi</Typography><Typography color="text.secondary">Kalıcı şirket verisi, yükleme geçmişi ve analiz uygunluğu yalnızca okunur olarak izlenir.</Typography></Box>
    {dataset.data && <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}><Metric label="Son kabul edilen yükleme" value={new Intl.DateTimeFormat('tr-TR', { dateStyle: 'medium' }).format(new Date(dataset.data.accepted_at))} /></Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}><Metric label="Son yükleme SKU" value={dataset.data.material_count} /></Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}><Metric label="Kalıcı aktif SKU" value={coverage?.total_scope_count ?? '—'} /></Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}><Metric label="Tam analiz edilebilir" value={coverage?.fully_analyzed_count ?? '—'} /></Grid>
    </Grid>}
    {readiness.isPending && <Typography role="status">Veri uygunluğu yükleniyor…</Typography>}
    {coverage && <Card variant="outlined"><CardContent><Stack spacing={1}>
      <Typography component="h2" variant="h6">Veri kalitesi ve analiz uygunluğu</Typography>
      <Typography variant="body2">Son yüklemede olmayan SKU: {coverage.absent_from_latest_upload_count} · Güncel snapshot uyarısı: {coverage.current_snapshot_warning_count} · Önceki yüklemeden taşınan master uyarısı: {coverage.stale_master_warning_count} · Kısmi analiz: {coverage.partially_analyzed_count} · Hariç tutulan: {coverage.excluded_count}</Typography>
      {coverage.exclusions.map((item, index) => <Alert key={`${item.material_code}-${item.capability}-${index}`} severity="warning"><strong>{item.product_name || item.material_code}</strong> · {item.message}</Alert>)}
    </Stack></CardContent></Card>}
  </Stack></Box>;
}
