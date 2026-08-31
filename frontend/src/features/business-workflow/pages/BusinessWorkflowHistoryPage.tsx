import { Alert, Box, Button, Card, CardContent, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { ROUTES } from '../../../constants/routes';
import { useAuth } from '../../../hooks/useAuth';
import { BusinessWorkflowTracking } from '../components/BusinessWorkflowTracking';
import { useBusinessWorkflowEntry } from '../useBusinessWorkflowEntry';

/** The API currently exposes company-scoped reads by execution id, not a history collection. */
export default function BusinessWorkflowHistoryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const entry = useBusinessWorkflowEntry(user?.company_id);

  return <Box sx={{ width: '100%', maxWidth: 1100, mx: 'auto' }}><Stack spacing={3}>
    <Box><Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>İşlem Geçmişi</Typography><Typography color="text.secondary">İşletme analizlerinizin durumunu ve kalıcı sonuçlarını takip edin.</Typography></Box>
    {entry.executionId ? <BusinessWorkflowTracking executionId={entry.executionId} onUnavailable={entry.clearUnavailableExecution} onStartAgain={entry.startBusinessWorkflow} /> : (
      <Card variant="outlined"><CardContent><Stack spacing={1.5} sx={{ alignItems: 'flex-start' }}>
        <Alert severity="info">Bu cihazda takip edilen bir işletme analizi yok.</Alert>
        <Typography color="text.secondary">Şirket kapsamlı işletme analizi geçmişi için listeleme API’si henüz sunulmuyor. Var olan bir çalışmanın sonuç bağlantısı, kalıcı sonuç ve karar kanıtlarını açmaya devam eder.</Typography>
        <Button variant="contained" onClick={() => navigate(ROUTES.BUSINESS_ANALYSIS)}>İşletme Analizine Git</Button>
      </Stack></CardContent></Card>
    )}
  </Stack></Box>;
}
