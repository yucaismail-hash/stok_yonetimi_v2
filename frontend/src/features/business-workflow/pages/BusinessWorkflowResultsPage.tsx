import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  Divider,
  Grid,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import { ROUTES } from '../../../constants/routes';
import {
  BusinessWorkflowApiError,
  type DecisionCandidatePresentation,
  type DecisionFinalizationPresentation,
  type DecisionPresentationItem,
  useBusinessWorkflowDecision,
  useExecution,
} from '../api';
import { executionStatusPresentation, presentWorkflowStage, safeFailureSummary } from '../executionPresentation';
import { AnalyticalEvidence } from '../components/results/AnalyticalEvidence';
import { DecisionFeedback } from '../components/results/DecisionFeedback';

function formatDate(value: string | null | undefined) {
  if (!value) return 'Belirtilmemiş';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('tr-TR', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function formatConfidence(value: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'percent', maximumFractionDigits: 0 }).format(value);
}

function decisionKey(item: DecisionPresentationItem) {
  return item.association.id;
}

function finalizationPresentation(finalization: DecisionFinalizationPresentation | null) {
  if (!finalization) return { severity: 'info' as const, title: 'Karar analizi henüz oluşturulmadı', description: 'Analitik iş akışı tamamlandıktan sonra karar analizi hazırlanır.' };
  switch (finalization.status) {
    case 'pending': return { severity: 'info' as const, title: 'Karar analizi bekliyor', description: 'Karar kanıtları hazırlanmak üzere sırada.' };
    case 'running': return { severity: 'info' as const, title: 'Karar analizi hazırlanıyor', description: 'Analitik sonuçlar korunur; karar analizi ayrı olarak tamamlanır.' };
    case 'partially_succeeded': return { severity: 'warning' as const, title: 'Karar analizi kısmen tamamlandı', description: 'Bazı malzemeler için karar kanıtı veya limitasyon mevcut.' };
    case 'failed': return { severity: 'warning' as const, title: 'Karar analizi tamamlanamadı', description: 'Analitik iş akışı tamamlandı; karar kanıtı daha sonra yeniden hazırlanabilir.' };
    case 'succeeded': return { severity: 'success' as const, title: 'Karar analizi hazır', description: 'Aşağıdaki kararlar kalıcı geçmiş kanıta dayanır.' };
  }
}

function candidateDescription(candidate: DecisionCandidatePresentation) {
  const parts = [candidate.candidate_type, candidate.severity && `Önem: ${candidate.severity}`, `Öncelik: ${candidate.priority}`].filter(Boolean);
  return parts.join(' · ');
}

function lifecycleErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'İş akışı durumu alınamadı. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'execution-unavailable') return 'İş akışı sonucu bulunamadı.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  return 'İş akışı durumu şu anda alınamıyor. Lütfen tekrar deneyin.';
}

function decisionErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'Karar görünümü alınamadı. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'execution-unavailable') return 'İş akışı sonucu bulunamadı.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  if (error.kind === 'service-unavailable') return 'Karar görünümü geçici olarak kullanılamıyor.';
  return 'Karar görünümü şu anda alınamıyor. Lütfen tekrar deneyin.';
}

function decisionValue(value: unknown) {
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return null;
}

function DecisionDetail({ executionId, decision }: { executionId: string; decision: DecisionPresentationItem }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const decisionEntries = Object.entries(decision.explanation.decision)
    .map(([key, value]) => [key, decisionValue(value)] as const)
    .filter((entry): entry is readonly [string, string] => entry[1] !== null);

  return (
    <Stack spacing={2}>
      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1}>
            <Typography component="h2" variant="h6">Stokonomi Önerisi</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
              <Chip label={`Güven: ${formatConfidence(decision.snapshot.confidence)}`} color="primary" />
              <Chip label={`Kanıt uyumu: ${decision.snapshot.agreement_status}`} variant="outlined" />
              <Chip label={`Durum: ${decision.snapshot.status}`} variant="outlined" />
            </Stack>
            <Typography color="text.secondary">{decision.association.material_code} · {decision.association.demand_type} · {decision.association.decision_context}</Typography>
            {decisionEntries.length > 0 && (
              <Stack spacing={0.5}>
                {decisionEntries.map(([key, value]) => <Typography key={key} variant="body2"><strong>{key}:</strong> {value}</Typography>)}
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>

      {(decision.snapshot.uncertainty_codes.length > 0 || decision.explanation.limitations.length > 0) && (
        <Alert severity="warning">
          <Typography component="div" variant="subtitle2">Dikkat Edilecek Noktalar</Typography>
          {decision.snapshot.uncertainty_codes.length > 0 && <Typography variant="body2">Belirsizlik: {decision.snapshot.uncertainty_codes.join(', ')}</Typography>}
          {decision.explanation.limitations.map((limitation) => <Typography key={limitation} variant="body2">{limitation}</Typography>)}
        </Alert>
      )}

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1}>
            <Typography component="h3" variant="h6">Neden Bu Öneri?</Typography>
            {decisionEntries.length === 0 && <Typography color="text.secondary">Bu karar için ek açıklama alanı yok.</Typography>}
            <Button onClick={() => setSourcesOpen((open) => !open)} aria-expanded={sourcesOpen} sx={{ alignSelf: 'flex-start' }}>
              {sourcesOpen ? 'Teknik kaynakları gizle' : 'Teknik kaynakları göster'}
            </Button>
            <Collapse in={sourcesOpen}>
              <Stack spacing={1}>
                {decision.explanation.source_provenance.map((source, index) => (
                  <Paper key={`${source.group}-${source.source}-${index}`} variant="outlined" sx={{ p: 1.25 }}>
                    <Typography variant="body2"><strong>{source.group}</strong> · {source.source}</Typography>
                    <Typography variant="caption" color="text.secondary">{source.semantic_type}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Collapse>
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1}>
            <Typography component="h3" variant="h6">Alternatifler</Typography>
            {decision.candidates.length === 0 && <Typography color="text.secondary">Kalıcı alternatif karar kaydı bulunmuyor.</Typography>}
            {decision.candidates.map((candidate) => (
              <Paper key={candidate.ordinal} variant="outlined" sx={{ p: 1.5 }}>
                <Typography variant="subtitle2">Alternatif {candidate.ordinal}</Typography>
                <Typography variant="body2">{candidateDescription(candidate)}</Typography>
                <Typography variant="body2">Güven: {formatConfidence(candidate.confidence)}</Typography>
                {candidate.reason_codes.length > 0 && <Typography variant="body2" color="text.secondary">Nedenler: {candidate.reason_codes.join(', ')}</Typography>}
              </Paper>
            ))}
          </Stack>
        </CardContent>
      </Card>
      <DecisionFeedback key={decision.snapshot.id} executionId={executionId} snapshotId={decision.snapshot.id} />
    </Stack>
  );
}

function finalizationLimitationLabel(limitation: Record<string, unknown>) {
  const materialCode = typeof limitation.material_code === 'string' ? limitation.material_code : null;
  return materialCode ? `${materialCode} için karar kanıtı tamamlanamadı.` : 'Bir malzeme için karar kanıtı tamamlanamadı.';
}

export default function BusinessWorkflowResultsPage() {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const execution = useExecution(executionId);
  const decision = useBusinessWorkflowDecision(
    executionId,
    Boolean(execution.data && executionStatusPresentation[execution.data.status].terminal),
  );
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | undefined>();

  const decisions = decision.data?.decisions ?? [];
  const filteredDecisions = useMemo(
    () => decisions.filter((item) => item.association.material_code.toLocaleLowerCase('tr-TR').includes(search.trim().toLocaleLowerCase('tr-TR'))),
    [decisions, search],
  );

  useEffect(() => {
    if (filteredDecisions.length === 0) return;
    if (!selectedKey || !filteredDecisions.some((item) => decisionKey(item) === selectedKey)) setSelectedKey(decisionKey(filteredDecisions[0]));
  }, [filteredDecisions, selectedKey]);

  if (!executionId) return <Alert severity="error" action={<Button color="inherit" onClick={() => navigate(ROUTES.DASHBOARD)}>Kontrol Paneline Dön</Button>}>İş akışı sonucu bulunamadı.</Alert>;
  if (execution.isPending) return <Card variant="outlined"><CardContent><Typography role="status">İş akışı sonuçları yükleniyor…</Typography></CardContent></Card>;
  if (execution.isError || !execution.data) return <Stack spacing={1}><Alert severity="warning">{lifecycleErrorMessage(execution.error)}</Alert><Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}><Button variant="outlined" onClick={() => execution.refetch()}>Tekrar dene</Button><Button variant="text" onClick={() => navigate(ROUTES.DASHBOARD)}>Kontrol Paneline Dön</Button></Stack></Stack>;

  const lifecycle = execution.data;
  const lifecyclePresentation = executionStatusPresentation[lifecycle.status];
  const workflowActive = !lifecyclePresentation.terminal;
  const selectedDecision = filteredDecisions.find((item) => decisionKey(item) === selectedKey);
  const finalization = decision.data?.decision_finalization ?? null;
  const finalizationState = finalizationPresentation(finalization);

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto' }}>
      <Stack spacing={3}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ justifyContent: 'space-between', alignItems: { sm: 'flex-start' } }}>
          <Box>
            <Typography component="h1" variant="h4" sx={{ fontWeight: 700 }}>İş Akışı Sonuçları</Typography>
            <Typography color="text.secondary">{lifecyclePresentation.title} · {formatDate(lifecycle.completed_at || lifecycle.started_at || lifecycle.created_at)}</Typography>
          </Box>
          <Button variant="outlined" onClick={() => navigate(ROUTES.DASHBOARD)}>Kontrol Paneline Dön</Button>
        </Stack>

        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
                <Chip label={lifecyclePresentation.title} color={lifecycle.status === 'completed' ? 'success' : lifecycle.status === 'failed' ? 'error' : 'primary'} />
                <Chip label={`İlerleme: %${Math.max(0, Math.min(100, lifecycle.progress))}`} variant="outlined" />
                {lifecycle.current_stage && <Chip label={`Adım: ${presentWorkflowStage(lifecycle.current_stage)}`} variant="outlined" />}
              </Stack>
              <Typography color="text.secondary">Veri seti bağlamı: çalışma sırasında kalıcı olarak kaydedildi.</Typography>
              {lifecycle.failure_summary && <Alert severity="error">{safeFailureSummary(lifecycle.failure_summary) || 'İş akışı tamamlanamadı.'}</Alert>}
            </Stack>
          </CardContent>
        </Card>

        {workflowActive && (
          <Alert severity="info" action={<Button color="inherit" onClick={() => navigate(ROUTES.DASHBOARD)}>Takibe dön</Button>}>
            İş akışı henüz tamamlanmadı. Karar sonucu hazır olduğunda bu sayfa kalıcı kanıtı gösterecek.
          </Alert>
        )}

        {!workflowActive && decision.isError && (
          <Alert severity="warning" action={<Button color="inherit" onClick={() => decision.refetch()}>Tekrar dene</Button>}>
            {decisionErrorMessage(decision.error)}
          </Alert>
        )}

        {!workflowActive && decision.isPending && <Alert severity="info" role="status">Karar kanıtları yükleniyor…</Alert>}

        {!workflowActive && decision.isSuccess && (
          <>
            <Alert severity={finalizationState.severity}>
              <Typography component="div" variant="subtitle2">{finalizationState.title}</Typography>
              <Typography variant="body2">{finalizationState.description}</Typography>
              {finalization && <Typography variant="body2">Tamamlanan malzeme: {finalization.completed_material_codes.length}</Typography>}
              {finalization?.limitations.map((limitation, index) => <Typography key={`${String(limitation.material_code ?? 'limitation')}-${index}`} variant="body2">{finalizationLimitationLabel(limitation)}</Typography>)}
            </Alert>

            {decisions.length === 0 ? (
              <Alert severity={finalization?.status === 'failed' ? 'warning' : 'info'}>
                {finalization?.status === 'failed'
                  ? 'Analitik sonuçlar tamamlandı ancak karar analizi tamamlanamadı.'
                  : finalization?.status === 'pending' || finalization?.status === 'running'
                    ? 'Karar analizi hazırlanıyor.'
                    : 'Bu çalışma için gösterilebilir bir karar önerisi oluşmadı.'}
              </Alert>
            ) : (
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card variant="outlined">
                    <CardContent>
                      <Stack spacing={1.5}>
                        <Typography component="h2" variant="h6">Malzemeler</Typography>
                        <TextField label="Malzeme ara" size="small" value={search} onChange={(event) => setSearch(event.target.value)} />
                        {/* TODO: Server-side Decision pagination/search is required before 22k-scale rendering. */}
                        <List dense aria-label="Karar malzeme listesi" sx={{ maxHeight: { xs: 260, md: 620 }, overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1 }}>
                          {filteredDecisions.map((item) => {
                            const selected = decisionKey(item) === selectedKey;
                            return <ListItemButton key={decisionKey(item)} selected={selected} onClick={() => setSelectedKey(decisionKey(item))} aria-current={selected ? 'true' : undefined}>
                              <ListItemText primary={item.association.material_code} secondary={`${item.association.demand_type} · ${formatConfidence(item.snapshot.confidence)}`} />
                            </ListItemButton>;
                          })}
                          {filteredDecisions.length === 0 && <Typography sx={{ p: 2 }} color="text.secondary">Aramanızla eşleşen malzeme yok.</Typography>}
                        </List>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid size={{ xs: 12, md: 8 }}>
                  {selectedDecision && <DecisionDetail executionId={executionId} decision={selectedDecision} />}
                </Grid>
              </Grid>
            )}

            <Divider />
            <AnalyticalEvidence executionId={executionId} selectedMaterialCode={selectedDecision?.association.material_code} />
          </>
        )}
      </Stack>
    </Box>
  );
}
