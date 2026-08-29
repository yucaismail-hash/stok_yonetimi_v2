import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Collapse,
  Divider,
  Pagination,
  Paper,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

import {
  BusinessWorkflowApiError,
  type BacktestResultItem,
  type BusinessWorkflowAggregateResult,
  type ForecastResultItem,
  type SafetyStockResultItem,
  type SimulationResultItem,
  type SupplierResultItem,
  useExecutionResult,
} from '../../api';

type ModuleId = 'forecast' | 'safety_stock' | 'simulation' | 'backtest' | 'supplier';

const moduleLabels: Record<ModuleId, string> = {
  forecast: 'Talep Tahmini',
  safety_stock: 'Emniyet Stoku',
  simulation: 'Simülasyon',
  backtest: 'Backtest',
  supplier: 'Tedarikçi',
};

const pageSize = 20;

function number(value: unknown, maximumFractionDigits = 2) {
  return typeof value === 'number' && Number.isFinite(value)
    ? new Intl.NumberFormat('tr-TR', { maximumFractionDigits }).format(value)
    : 'Veri yok';
}

function percentage(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value)
    ? new Intl.NumberFormat('tr-TR', { style: 'percent', maximumFractionDigits: 1 }).format(value)
    : 'Veri yok';
}

function warningText(value: unknown) {
  return typeof value === 'string' ? value : null;
}

function humanMetricLabel(key: string) {
  const labels: Record<string, string> = {
    processed_skus: 'İşlenen malzeme',
    candidate_method_count: 'Yöntem sayısı',
    service_level: 'Servis seviyesi',
    total_cost: 'Toplam maliyet',
    total_shortage: 'Toplam eksik',
    stockout_probability: 'Stok tükenme olasılığı',
  };
  return labels[key] || key.replace(/_/g, ' ');
}

function MetricGrid({ metrics }: { metrics?: Record<string, unknown> }) {
  const entries = Object.entries(metrics ?? {}).filter(([key, value]) => key !== 'adapter_duration_ms' && (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'));
  if (entries.length === 0) return null;
  return (
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
      {entries.map(([key, value]) => (
        <Paper key={key} variant="outlined" sx={{ p: 1.25, minWidth: 140 }}>
          <Typography variant="caption" color="text.secondary">{humanMetricLabel(key)}</Typography>
          <Typography variant="body2" sx={{ fontWeight: 700 }}>{typeof value === 'number' ? number(value) : String(value)}</Typography>
        </Paper>
      ))}
    </Stack>
  );
}

function WarningsList({ warnings }: { warnings?: unknown[] }) {
  const visibleWarnings = (warnings ?? []).map(warningText).filter((value): value is string => Boolean(value));
  if (visibleWarnings.length === 0) return null;
  return <Alert severity="warning"><Typography component="div" variant="subtitle2">Uyarılar</Typography>{visibleWarnings.map((warning) => <Typography key={warning} variant="body2">{warning}</Typography>)}</Alert>;
}

function moduleIds(result: BusinessWorkflowAggregateResult): ModuleId[] {
  const ids: ModuleId[] = [];
  if (result.forecast) ids.push('forecast');
  if (result.safety_stock) ids.push('safety_stock');
  if (result.simulation) ids.push('simulation');
  if (result.backtest) ids.push('backtest');
  if (result.supplier) ids.push('supplier');
  return ids;
}

function MaterialTable({ children }: { children: React.ReactNode }) {
  return <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 520 }}><Table stickyHeader size="small" aria-label="Analitik kanıt tablosu">{children}</Table></TableContainer>;
}

function ForecastAdapter({ items, horizon }: { items: ForecastResultItem[]; horizon?: number }) {
  return <MaterialTable><TableHead><TableRow><TableCell>Malzeme</TableCell><TableCell>Model</TableCell><TableCell>Tahmin ufku</TableCell><TableCell>Tahmin değerleri</TableCell></TableRow></TableHead><TableBody>
    {items.map((item) => <TableRow key={item.material_code}><TableCell>{item.material_code}</TableCell><TableCell>{item.model_used || 'Veri yok'}</TableCell><TableCell>{horizon ?? item.forecast.length}</TableCell><TableCell>{item.forecast.length > 0 ? `${item.forecast.slice(0, 6).map((value) => number(value)).join(', ')}${item.forecast.length > 6 ? '…' : ''}` : 'Veri yok'}</TableCell></TableRow>)}
  </TableBody></MaterialTable>;
}

function SafetyStockAdapter({ items }: { items: SafetyStockResultItem[] }) {
  return <MaterialTable><TableHead><TableRow><TableCell>Malzeme</TableCell><TableCell>Önerilen emniyet stoku</TableCell><TableCell>Servis seviyesi</TableCell><TableCell>Lead time</TableCell><TableCell>Yöntem</TableCell></TableRow></TableHead><TableBody>
    {items.map((item) => <TableRow key={item.material_code}><TableCell>{item.material_code}</TableCell><TableCell>{number(item.safety_stock)}</TableCell><TableCell>{percentage(item.service_level)}</TableCell><TableCell>{item.effective_lead_time_used === undefined ? 'Veri yok' : `${number(item.effective_lead_time_used)} ${item.effective_unit || 'gün'}`}</TableCell><TableCell>{item.selected_method || 'Veri yok'}</TableCell></TableRow>)}
  </TableBody></MaterialTable>;
}

function SimulationAdapter({ items }: { items: SimulationResultItem[] }) {
  return <MaterialTable><TableHead><TableRow><TableCell>Malzeme</TableCell><TableCell>Servis seviyesi</TableCell><TableCell>CVaR %95</TableCell><TableCell>ROP</TableCell><TableCell>Hafta</TableCell></TableRow></TableHead><TableBody>
    {items.map((item) => <TableRow key={item.material_code}><TableCell>{item.material_code}</TableCell><TableCell>{percentage(item.service_level)}</TableCell><TableCell>{number(item.cvar_95)}</TableCell><TableCell>{number(item.rop)}</TableCell><TableCell>{item.weeks ?? 'Veri yok'}</TableCell></TableRow>)}
  </TableBody></MaterialTable>;
}

function BacktestAdapter({ items }: { items: BacktestResultItem[] }) {
  return <MaterialTable><TableHead><TableRow><TableCell>Malzeme</TableCell><TableCell>Doğrulanan strateji</TableCell><TableCell>Toplam maliyet</TableCell><TableCell>Servis seviyesi</TableCell><TableCell>Test penceresi</TableCell></TableRow></TableHead><TableBody>
    {items.map((item) => {
      const metrics = item.validated_strategy ? item.metrics?.[item.validated_strategy] : undefined;
      return <TableRow key={item.material_code}><TableCell>{item.material_code}</TableCell><TableCell>{item.validated_strategy || 'Veri yok'}</TableCell><TableCell>{number(metrics?.total_cost)}</TableCell><TableCell>{percentage(metrics?.service_level)}</TableCell><TableCell>{item.test_window ?? 'Veri yok'}</TableCell></TableRow>;
    })}
  </TableBody></MaterialTable>;
}

function SupplierAdapter({ items }: { items: SupplierResultItem[] }) {
  return <MaterialTable><TableHead><TableRow><TableCell>Tedarikçi</TableCell><TableCell>Performans</TableCell><TableCell>Risk</TableCell><TableCell>Ortalama lead time</TableCell><TableCell>Malzeme eşleşmesi</TableCell></TableRow></TableHead><TableBody>
    {items.map((item) => <TableRow key={item.supplier_id}><TableCell>{item.name || item.supplier_id}</TableCell><TableCell>{number(item.performance_score)}</TableCell><TableCell>{number(item.risk_score)}</TableCell><TableCell>{number(item.lead_time_mean)}</TableCell><TableCell>{item.material_mappings?.map((mapping) => mapping.material_code).join(', ') || 'Veri yok'}</TableCell></TableRow>)}
  </TableBody></MaterialTable>;
}

function resultErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'Analitik sonuçlar yüklenemedi. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'execution-unavailable') return 'Analitik sonuçlar bulunamadı.';
  if (error.kind === 'result-not-ready') return 'Analitik sonuçlar henüz hazır değil.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  return 'Analitik sonuçlar yüklenemedi. Lütfen tekrar deneyin.';
}

export function AnalyticalEvidence({ executionId, selectedMaterialCode }: { executionId: string; selectedMaterialCode?: string }) {
  const [activated, setActivated] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const resultQuery = useExecutionResult(executionId, activated);
  const result = resultQuery.data?.result;
  const modules = useMemo(() => result ? moduleIds(result) : [], [result]);
  const [activeModule, setActiveModule] = useState<ModuleId>('forecast');
  const [selectedOnly, setSelectedOnly] = useState(Boolean(selectedMaterialCode));
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (modules.length > 0 && !modules.includes(activeModule)) setActiveModule(modules[0]);
  }, [activeModule, modules]);

  useEffect(() => setPage(1), [activeModule, selectedOnly, selectedMaterialCode]);

  const activate = () => {
    setActivated(true);
    setExpanded(true);
  };

  const currentItems = useMemo(() => {
    if (!result) return [] as Record<string, unknown>[];
    if (activeModule === 'supplier') return result.supplier?.suppliers ?? [];
    return result[activeModule]?.items ?? [];
  }, [activeModule, result]);
  const filteredItems = useMemo(() => {
    if (!selectedOnly || !selectedMaterialCode || activeModule === 'supplier') return currentItems;
    return currentItems.filter((item) => item.material_code === selectedMaterialCode);
  }, [activeModule, currentItems, selectedMaterialCode, selectedOnly]);
  const pageCount = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const visibleItems = filteredItems.slice((page - 1) * pageSize, page * pageSize);

  return (
    <Card variant="outlined" id="analytical-evidence">
      <CardContent>
        <Stack spacing={2}>
          <Box>
            <Typography component="h2" variant="h6">Analitik Sonuçları İncele</Typography>
            <Typography color="text.secondary">Forecast, Emniyet Stoku, Simülasyon ve Backtest ayrıntıları karar kanıtını destekler.</Typography>
          </Box>

          {!activated && <Button variant="outlined" onClick={activate} aria-label="Analitik sonuçları yükle">Analitik Sonuçları İncele</Button>}

          {activated && <Button variant="text" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded} sx={{ alignSelf: 'flex-start' }}>{expanded ? 'Analitik ayrıntıları gizle' : 'Analitik ayrıntıları göster'}</Button>}

          <Collapse in={expanded}>
            <Stack spacing={2} sx={{ pt: 1 }}>
              {resultQuery.isPending && <Typography role="status">Analitik sonuçlar yükleniyor…</Typography>}
              {resultQuery.isError && <Alert severity="warning" action={<Button color="inherit" onClick={() => resultQuery.refetch()}>Tekrar dene</Button>}>{resultErrorMessage(resultQuery.error)}</Alert>}
              {resultQuery.isSuccess && result && (
                <>
                  {modules.length === 0 ? <Alert severity="info">Bu çalışma için analitik sonuç paketi bulunmuyor.</Alert> : <>
                    <Tabs value={activeModule} onChange={(_, value: ModuleId) => setActiveModule(value)} variant="scrollable" scrollButtons="auto" aria-label="Analitik modüller">
                      {modules.map((module) => <Tab key={module} value={module} label={moduleLabels[module]} />)}
                    </Tabs>

                    {selectedMaterialCode && activeModule !== 'supplier' && <Button variant="text" onClick={() => setSelectedOnly((value) => !value)} sx={{ alignSelf: 'flex-start' }}>{selectedOnly ? `Tüm malzemeleri göster` : `Seçili SKU (${selectedMaterialCode}) için kanıtı göster`}</Button>}

                    {activeModule === 'forecast' && <MetricGrid metrics={{ horizon: result.forecast?.horizon, ...result.forecast?.metrics }} />}
                    {activeModule === 'safety_stock' && <MetricGrid metrics={{ service_level: result.safety_stock?.service_level, ...result.safety_stock?.metrics }} />}
                    {activeModule === 'simulation' && <MetricGrid metrics={result.simulation?.metrics} />}
                    {activeModule === 'backtest' && <MetricGrid metrics={result.backtest?.metrics} />}
                    {activeModule === 'supplier' && <MetricGrid metrics={{ mapping_count: result.supplier?.mapping_count }} />}

                    {filteredItems.length === 0 ? <Alert severity="info">Bu görünüm için veri yok.</Alert> : <>
                      {activeModule === 'forecast' && <ForecastAdapter items={visibleItems as ForecastResultItem[]} horizon={result.forecast?.horizon} />}
                      {activeModule === 'safety_stock' && <SafetyStockAdapter items={visibleItems as SafetyStockResultItem[]} />}
                      {activeModule === 'simulation' && <SimulationAdapter items={visibleItems as SimulationResultItem[]} />}
                      {activeModule === 'backtest' && <BacktestAdapter items={visibleItems as BacktestResultItem[]} />}
                      {activeModule === 'supplier' && <SupplierAdapter items={visibleItems as SupplierResultItem[]} />}
                      {pageCount > 1 && <Pagination count={pageCount} page={Math.min(page, pageCount)} onChange={(_, value) => setPage(value)} aria-label="Analitik sonuç sayfaları" />}
                    </>}

                    {activeModule !== 'supplier' && <WarningsList warnings={result[activeModule]?.warnings} />}
                    {activeModule === 'supplier' && <Typography color="text.secondary">Tedarikçi analizi yalnızca bu iş akışında kalıcı kanıt mevcut olduğunda gösterilir.</Typography>}
                    <Divider />
                    <TechnicalProvenance provenance={result.provenance} />
                  </>}
                </>
              )}
            </Stack>
          </Collapse>
        </Stack>
      </CardContent>
    </Card>
  );
}

function TechnicalProvenance({ provenance }: { provenance?: Record<string, string> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(provenance ?? {});
  if (entries.length === 0) return null;
  return <Box><Button variant="text" onClick={() => setOpen((value) => !value)} aria-expanded={open}>{open ? 'Teknik ayrıntıları gizle' : 'Teknik ayrıntıları göster'}</Button><Collapse in={open}><Stack spacing={0.5} sx={{ pt: 1 }}>{entries.map(([label, reference]) => <Typography key={label} variant="caption" sx={{ overflowWrap: 'anywhere' }}>{label}: {reference}</Typography>)}</Stack></Collapse></Box>;
}
