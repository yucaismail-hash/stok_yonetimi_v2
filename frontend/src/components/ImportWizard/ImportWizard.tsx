import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, List, ListItem, ListItemText, Typography } from '@mui/material';
import Step1FileUpload from './Step1FileUpload';
import { acceptPilotDataset, downloadPilotTemplate, PilotUploadResponse, uploadPilotDataset } from '../../features/dataset/api/pilotDatasetApi';
import { pilotDatasetKeys } from '../../features/dataset/api/pilotDatasetQueries';

interface ImportWizardProps { open: boolean; onClose: () => void; onComplete: (datasetId: string) => void; }

export default function ImportWizard({ open, onClose, onComplete }: ImportWizardProps) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<PilotUploadResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const reset = () => { setFile(null); setValidation(null); setLoading(false); setError(null); setAccepted(false); };
  const close = () => { if (!loading) { reset(); onClose(); } };

  const selectFile = async (selected: File) => {
    setFile(selected); setValidation(null); setError(null); setLoading(true);
    try { setValidation(await uploadPilotDataset(selected)); }
    catch (cause: any) { setError(cause.response?.data?.detail || 'Dosya doğrulanamadı. Lütfen tekrar deneyin.'); }
    finally { setLoading(false); }
  };

  const accept = async () => {
    if (!validation?.READY_FOR_ACCEPTANCE) return;
    setError(null); setLoading(true);
    try {
      const accepted = await acceptPilotDataset(validation.dataset_id);
      localStorage.setItem('activeDatasetId', accepted.dataset_id);
      localStorage.setItem('activeDatasetStatus', accepted.status);
      void queryClient.invalidateQueries({ queryKey: pilotDatasetKeys.all });
      setValidation({ ...validation, status: accepted.status, READY_FOR_ACCEPTANCE: false });
      setAccepted(true);
      onComplete(accepted.dataset_id);
    } catch (cause: any) { setError(cause.response?.data?.detail || 'Dataset kabul edilemedi. Lütfen tekrar deneyin.'); }
    finally { setLoading(false); }
  };
  const downloadTemplate = async () => { setError(null); setDownloading(true); try { await downloadPilotTemplate(); } catch { setError('Şablon indirilemedi. Lütfen tekrar deneyin.'); } finally { setDownloading(false); } };

  return <Dialog open={open} onClose={close} fullWidth maxWidth="md">
    <DialogTitle>İlk veri setinizi hazırlayın</DialogTitle>
    <DialogContent dividers>
      {!validation ? <><Alert severity="info" sx={{ mb: 2 }}>Pilot şablonu; Malzeme Kodu, Talep Tipi, Ürün Seviyesi, Dönem ve Miktar alanlarını içerir.</Alert><Button onClick={downloadTemplate} disabled={loading || downloading} sx={{ mb: 2 }}>Excel Şablonunu İndir</Button><Step1FileUpload file={file} onFileSelect={selectFile} loading={loading} error={error} /></> : <Box>
        <Typography variant="h6" gutterBottom>Doğrulama sonucu</Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip label={`${validation.summary.record_count} kayıt`} />
          <Chip label={`${validation.summary.material_count} malzeme`} />
          <Chip label={validation.status} color={validation.READY_FOR_ACCEPTANCE ? 'success' : 'error'} />
        </Box>
        {validation.same_file_retry && <Alert severity="info" sx={{ mb: 2 }}>Aynı dosyanın mevcut doğrulama sonucu kullanıldı.</Alert>}
        {validation.warnings.length > 0 && <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">{validation.warnings.length} uyarı bulundu</Typography>
          <List dense>{validation.warnings.map((warning, index) =>
            <ListItem key={`${warning.code}-${index}`} disablePadding><ListItemText primary={warning.message} /></ListItem>
          )}</List>
        </Alert>}
        {validation.issues.length > 0 && <Alert severity="error" sx={{ mb: 2 }}><List dense>{validation.issues.map((issue, index) =>
          <ListItem key={`${issue.code}-${index}`} disablePadding><ListItemText primary={issue.message} secondary={[issue.sheet, issue.row && `satır ${issue.row}`, issue.column].filter(Boolean).join(' · ')} /></ListItem>
        )}</List></Alert>}
        {accepted ? <Alert severity="success">Veriler kullanıma hazır. Analiz veya iş akışı daha sonra başlatılabilir.</Alert> : validation.READY_FOR_ACCEPTANCE ? <Alert severity="success">Dosya doğrulandı. Veriyi Kabul Et ile kullanıma hazır hale getirebilirsiniz.</Alert> : <Alert severity="error">Hatalar düzeltilmeden veri kabul edilemez.</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </Box>}
    </DialogContent>
    <DialogActions>
      <Button onClick={close} disabled={loading}>Kapat</Button>
      {validation && <Button onClick={() => { setValidation(null); setFile(null); }} disabled={loading}>Başka dosya seç</Button>}
      {validation?.READY_FOR_ACCEPTANCE && <Button variant="contained" onClick={accept} disabled={loading}>{loading ? <CircularProgress size={20} /> : 'Veriyi Kabul Et'}</Button>}
    </DialogActions>
  </Dialog>;
}
