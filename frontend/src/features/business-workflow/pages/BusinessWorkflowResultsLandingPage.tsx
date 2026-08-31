import { Alert, Box, Button, Card, CardContent, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { ROUTES } from '../../../constants/routes';
import { useAuth } from '../../../hooks/useAuth';
import { BusinessWorkflowTracking } from '../components/BusinessWorkflowTracking';
import { useBusinessWorkflowEntry } from '../useBusinessWorkflowEntry';

/** Results remain execution-scoped so a read never selects a "latest" Decision. */
export default function BusinessWorkflowResultsLandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const entry = useBusinessWorkflowEntry(user?.company_id);

  return <Box sx={{ width: '100%', maxWidth: 1100, mx: 'auto' }}><Stack spacing={3}>
    <Box><Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>Sonuçlar & Kararlar</Typography><Typography color="text.secondary">Tamamlanan işletme analizinize ait kalıcı sonuçları ve karar kanıtlarını görüntüleyin.</Typography></Box>
    {entry.executionId ? <BusinessWorkflowTracking executionId={entry.executionId} onUnavailable={entry.clearUnavailableExecution} onStartAgain={entry.startBusinessWorkflow} /> : (
      <Card variant="outlined"><CardContent><Stack spacing={1.5} sx={{ alignItems: 'flex-start' }}>
        <Alert severity="info">Görüntülenecek bir işletme analizi seçilmedi.</Alert>
        <Typography color="text.secondary">Sonuçlar, doğru işleme ait kalıcı kanıtı korumak için yürütme kimliğiyle açılır. Yeni bir işletme analizi başlattığınızda bu ekran mevcut çalışmayı takip eder.</Typography>
        <Button variant="contained" onClick={() => navigate(ROUTES.BUSINESS_ANALYSIS)}>İşletme Analizine Git</Button>
      </Stack></CardContent></Card>
    )}
  </Stack></Box>;
}
