// frontend/src/components/ImportWizard/ImportWizard.tsx
// Smart Import Engine - Ana Wizard Bileşeni
import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  LinearProgress,
  Chip,
  Button,
  Stepper,
  Step,
  StepLabel,
  Alert,
} from '@mui/material';
import { Close, AutoAwesome, ArrowBack, ArrowForward } from '@mui/icons-material';
import { validateExcel, createDataset } from '../../services/api';
import { ValidationResponse } from '../../types/import';

// Step bileşenleri
import Step1FileUpload from './Step1FileUpload';
import Step2SheetCheck from './Step2SheetCheck';
import Step3DataValidation from './Step3DataValidation';
import Step4QualityAnalysis from './Step4QualityAnalysis';
import Step5ImpactAnalysis from './Step5ImpactAnalysis';
import Step6Summary from './Step6Summary';

interface ImportWizardProps {
  open: boolean;
  onClose: () => void;
  onComplete: (datasetId: number) => void;
}

const steps = [
  'Excel Dosyası',
  'Sheet Kontrolü',
  'Veri Kalitesi',
  'Analiz ve Etki',
  'Impact Skorları',
  'Son Onay',
];

export default function ImportWizard({ open, onClose, onComplete }: ImportWizardProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationData, setValidationData] = useState<ValidationResponse | null>(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [canProceed, setCanProceed] = useState(true);

  // ============================================================
  // Wizard'ı kapatırken state resetle
  // ============================================================
  const handleClose = () => {
    if (processing) return;
    resetWizard();
    onClose();
  };

  const resetWizard = () => {
    setActiveStep(0);
    setFile(null);
    setUploadId(null);
    setLoading(false);
    setError(null);
    setValidationData(null);
    setProcessing(false);
    setProgress(0);
    setCanProceed(true);
  };

  // ============================================================
  // Dosya yükleme ve validasyon
  // ============================================================
  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setLoading(true);
    setProgress(10);

    try {
      const response = await validateExcel(selectedFile);
      const data = response.data;

      if (data.success) {
        setUploadId(data.upload_id);
        setValidationData(data);
        setCanProceed(data.can_proceed !== false);
        setProgress(100);
        setActiveStep(1);
      } else {
        setError(data.error || 'Dosya doğrulanamadı');
      }
    } catch (err: any) {
      console.error('❌ Validasyon hatası:', err);
      setError(err.response?.data?.detail || 'Dosya yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Dataset oluşturma
  // ============================================================
  const handleComplete = async () => {
    if (!uploadId) return;

    if (!canProceed) {
      setError('Kritik hatalar nedeniyle dataset oluşturulamaz.');
      return;
    }

    setProcessing(true);
    setProgress(0);

    try {
      setProgress(50);
      const datasetResponse = await createDataset(uploadId);
      
      if (!datasetResponse.data.success) {
        setError(datasetResponse.data.error || 'Dataset oluşturulamadı');
        setProcessing(false);
        return;
      }

      const datasetId = datasetResponse.data.dataset_id;
      setProgress(100);
      
      onComplete(datasetId);
      onClose();
    } catch (err: any) {
      console.error('❌ Dataset oluşturma hatası:', err);
      setError(err.response?.data?.detail || 'Dataset oluşturulamadı');
    } finally {
      setProcessing(false);
    }
  };

  // ============================================================
  // Navigasyon
  // ============================================================
  const handleNext = () => {
    // can_proceed adım geçişini engellemez! Sadece final buton disabled
    if (activeStep === steps.length - 1) {
      handleComplete();
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  // ============================================================
  // Step içeriğini render et
  // ============================================================
  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Step1FileUpload
            file={file}
            onFileSelect={handleFileSelect}
            loading={loading}
            error={error}
          />
        );
      case 1:
        return (
          <Step2SheetCheck
            data={validationData?.sheet_check}
            loading={loading}
          />
        );
      case 2:
        return (
          <Step3DataValidation
            data={validationData?.data_quality}
            loading={loading}
          />
        );
      case 3:
        return (
          <Step4QualityAnalysis
            data={validationData}
            loading={loading}
          />
        );
      case 4:
        return (
          <Step5ImpactAnalysis
            data={validationData?.impact}
            loading={loading}
          />
        );
      case 5:
        return (
          <Step6Summary
            data={validationData}
            loading={loading || processing}
            canProceed={canProceed}
            onComplete={handleComplete}
          />
        );
      default:
        return null;
    }
  };

  // ============================================================
  // Buton durumları
  // ============================================================
  const isFirstStep = activeStep === 0;
  const isLastStep = activeStep === steps.length - 1;
  
  // Adım tamamlandı mı?
  const isStepComplete = (step: number) => {
    if (step === 0) return !!file;
    if (step === 1) return validationData?.sheet_check?.success !== undefined;
    if (step === 2) return validationData?.data_quality !== undefined;
    if (step === 3) return validationData?.data_quality !== undefined;
    if (step === 4) return validationData?.impact !== undefined;
    if (step === 5) return true;
    return false;
  };

  const canNext = isStepComplete(activeStep);

  // ============================================================
  // useEffect: Wizard açıldığında reset
  // ============================================================
  useEffect(() => {
    if (open) {
      resetWizard();
    }
  }, [open]);

  // ============================================================
  // RENDER
  // ============================================================
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      slotProps={{
        paper: {
          sx: { minHeight: '70vh', maxHeight: '90vh' },
        },
      }}
    >
      <DialogTitle sx={{ borderBottom: '1px solid #f0f0f0', py: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AutoAwesome sx={{ color: '#1f4e79' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#1f4e79' }}>
              📥 Smart Import Engine
            </Typography>
            <Chip
              label={`Adım ${activeStep + 1}/${steps.length}`}
              size="small"
              sx={{ bgcolor: '#e8f0fe', color: '#1f4e79', fontSize: '0.65rem' }}
            />
          </Box>
          {!processing && (
            <IconButton onClick={handleClose} size="small">
              <Close />
            </IconButton>
          )}
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {/* İlerleme */}
        {(loading || processing) && (
          <Box sx={{ px: 3, pt: 2 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {loading ? 'Dosya doğrulanıyor...' : 'Dataset oluşturuluyor...'} %{Math.round(progress)}
            </Typography>
          </Box>
        )}

        {/* Hata mesajı */}
        {error && (
          <Alert severity="error" sx={{ mx: 3, mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Stepper */}
        <Box sx={{ px: 3, py: 2 }}>
          <Stepper activeStep={activeStep} orientation="horizontal" sx={{ overflowX: 'auto' }}>
            {steps.map((label, index) => (
              <Step key={label} completed={isStepComplete(index)}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {/* Step içeriği */}
        <Box sx={{ px: 3, py: 2, minHeight: 300 }}>
          {renderStepContent(activeStep)}
        </Box>
      </DialogContent>

      <DialogActions sx={{ borderTop: '1px solid #f0f0f0', py: 2, px: 3 }}>
        <Button
          onClick={handleClose}
          disabled={processing}
          sx={{ fontSize: '0.75rem', textTransform: 'none' }}
        >
          İptal
        </Button>
        <Box sx={{ flex: 1 }} />
        <Button
          onClick={handleBack}
          disabled={isFirstStep || processing}
          startIcon={<ArrowBack />}
          sx={{ fontSize: '0.75rem', textTransform: 'none' }}
        >
          Geri
        </Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={!canNext || processing}
          endIcon={!isLastStep ? <ArrowForward /> : undefined}
          sx={{
            bgcolor: '#1f4e79',
            '&:hover': { bgcolor: '#1a3d5c' },
            fontSize: '0.75rem',
            textTransform: 'none',
            borderRadius: 2,
            px: 3,
          }}
        >
          {isLastStep ? 'Dataset Oluştur' : 'İleri'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}