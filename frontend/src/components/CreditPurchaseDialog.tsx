import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Grid,
  Divider,
  Paper,
  Fade,
} from '@mui/material';
import { 
  CreditCard, 
  Close, 
  CheckCircle, 
  Payments, 
  ErrorOutlined,
  CancelOutlined,
  ShoppingCart,
} from '@mui/icons-material';
import api from '../services/api';

interface CreditPackage {
  id: number;
  polar_product_id: string;
  name: string;
  credits: number;
  price_tl: number;
  is_active: boolean;
}

interface CreditPurchaseDialogProps {
  open: boolean;
  onClose: () => void;
  onPurchase: (pkg: CreditPackage) => void;
  currentBalance: number;
  isLoading?: boolean;
  paymentStatus?: 'idle' | 'processing' | 'success' | 'canceled' | 'error';
  paymentMessage?: string | null;
  onReset?: () => void;
}

export default function CreditPurchaseDialog({
  open,
  onClose,
  onPurchase,
  currentBalance,
  isLoading = false,
  paymentStatus = 'idle',
  paymentMessage = null,
  onReset,
}: CreditPurchaseDialogProps) {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<CreditPackage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && paymentStatus === 'idle') {
      fetchPackages();
    }
  }, [open, paymentStatus]);

  const fetchPackages = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/polar/packages');
      if (res.data && Array.isArray(res.data)) {
        setPackages(res.data);
        if (res.data.length > 0) {
          setSelectedPackage(res.data[0]);
        }
      }
    } catch (error) {
      console.error('❌ Paket hatası:', error);
      setError('Paketler yüklenirken bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = () => {
    if (!selectedPackage) return;
    onPurchase(selectedPackage);
  };

  const handleClose = () => {
    setError(null);
    if (onReset) onReset();
    onClose();
  };

  // ✅ Ödeme durumuna göre içerik
  const renderContent = () => {
    // 🔄 İşlem Devam Ediyor
    if (isLoading) {
      return (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 3, fontWeight: 'bold', color: 'primary.main' }}>
            🚀 Ödeme Başlatılıyor...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Lütfen bekleyin, güvenli ödeme sayfası açılıyor.
          </Typography>
        </Box>
      );
    }

    // ✅ Ödeme Başarılı
    if (paymentStatus === 'success') {
      return (
        <Fade in timeout={500}>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              🎉 Ödeme Başarılı!
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              {paymentMessage || 'Kredileriniz hesabınıza başarıyla eklendi.'}
            </Typography>
            <Chip 
              label={`💰 Yeni Bakiye: ${currentBalance} Kredi`}
              color="success"
              sx={{ mt: 2, fontWeight: 'bold' }}
            />
          </Box>
        </Fade>
      );
    }

    // ⏹️ Ödeme İptal Edildi
    if (paymentStatus === 'canceled') {
      return (
        <Fade in timeout={500}>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CancelOutlined sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
              ⏹️ Ödeme İptal Edildi
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              {paymentMessage || 'Ödeme işleminiz iptal edildi. Herhangi bir ücret alınmamıştır.'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Tekrar denemek için aşağıdaki butonu kullanabilirsiniz.
            </Typography>
          </Box>
        </Fade>
      );
    }

    // ❌ Ödeme Hatası
    if (paymentStatus === 'error') {
      return (
        <Fade in timeout={500}>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <ErrorOutlined sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'error.main' }}>
              ❌ Ödeme Alınamadı
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              {paymentMessage || 'Ödeme işlemi sırasında bir hata oluştu.'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Lütfen tekrar deneyin veya farklı bir ödeme yöntemi kullanın.
            </Typography>
          </Box>
        </Fade>
      );
    }

    // 📦 Paket Seçim Ekranı (idle)
    return (
      <>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Aşağıdaki paketlerden birini seçerek kredi satın alabilirsiniz.
          Ödeme işlemi güvenli ödeme platformu Polar üzerinden gerçekleştirilir.
        </Typography>

        <Grid container spacing={2}>
          {packages.map((pkg) => (
            <Grid size={{ xs: 12, sm: 4 }} key={pkg.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: selectedPackage?.id === pkg.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                  transition: 'all 0.3s ease',
                  borderRadius: 3,
                  position: 'relative',
                  overflow: 'hidden',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 8,
                  },
                  ...(selectedPackage?.id === pkg.id && {
                    boxShadow: '0 8px 25px rgba(25, 118, 210, 0.25)',
                  }),
                }}
                onClick={() => setSelectedPackage(pkg)}
              >
                {selectedPackage?.id === pkg.id && (
                  <Box sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    bgcolor: 'success.main',
                    color: 'white',
                    px: 2,
                    py: 0.5,
                    borderRadius: '0 0 0 12px',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                  }}>
                    SEÇİLDİ
                  </Box>
                )}
                <CardContent sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {pkg.credits}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Kredi</Typography>
                  
                  <Divider sx={{ my: 1.5 }} />
                  
                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1a237e' }}>
                    ₺{pkg.price_tl.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {pkg.name}
                  </Typography>
                  
                  {selectedPackage?.id === pkg.id && (
                    <CheckCircle sx={{ color: 'success.main', mt: 1 }} />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {selectedPackage && (
          <Paper sx={{ 
            mt: 3, 
            p: 2.5, 
            bgcolor: '#e3f2fd', 
            borderRadius: 3,
            border: '1px solid #90caf9',
          }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                  📋 Seçilen Paket: {selectedPackage.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedPackage.credits} Kredi
                </Typography>
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                ₺{selectedPackage.price_tl.toFixed(2)}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              🔒 Güvenli ödeme Polar tarafından sağlanmaktadır.
            </Typography>
          </Paper>
        )}
      </>
    );
  };

  // ✅ Dialog Actions - Duruma göre butonlar
  const renderActions = () => {
    // İşlem devam ederken butonlar pasif
    if (isLoading) {
      return (
        <>
          <Button disabled>İptal</Button>
          <Button disabled variant="contained">
            <CircularProgress size={20} sx={{ mr: 1 }} />
            İşlem Devam Ediyor...
          </Button>
        </>
      );
    }

    // Başarılı veya iptal durumunda "Tamam" butonu
    if (paymentStatus === 'success' || paymentStatus === 'canceled') {
      return (
        <>
          <Button variant="contained" color="primary" onClick={handleClose}>
            {paymentStatus === 'success' ? 'Dashboard\'a Dön' : 'Tekrar Dene'}
          </Button>
        </>
      );
    }

    // Hata durumunda "Tekrar Dene" butonu
    if (paymentStatus === 'error') {
      return (
        <>
          <Button onClick={handleClose}>Vazgeç</Button>
          <Button variant="contained" color="warning" onClick={onReset}>
            Tekrar Dene
          </Button>
        </>
      );
    }

    // Normal durum (idle) - İptal ve Satın Al
    return (
      <>
        <Button 
          onClick={handleClose} 
          sx={{ 
            color: '#666',
            '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' }
          }}
        >
          İptal
        </Button>
        <Button
          variant="contained"
          onClick={handlePurchase}
          disabled={!selectedPackage || loading}
          startIcon={<Payments />}
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #0d47a1 0%, #1a237e 100%)',
            },
            '&:disabled': {
              background: '#ccc',
            },
          }}
        >
          Satın Al
        </Button>
      </>
    );
  };

  return (
    <Dialog 
      open={open} 
      onClose={paymentStatus === 'idle' ? handleClose : undefined}
      maxWidth="sm" 
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
            overflow: 'hidden',
            minHeight: 400,
          }
        }
      }}
    >
      {/* Header - Gradient */}
      <Box sx={{ 
        p: 3, 
        background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
        color: 'white',
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
              {paymentStatus === 'success' ? '✅ Ödeme Başarılı' :
               paymentStatus === 'canceled' ? '⏹️ Ödeme İptal' :
               paymentStatus === 'error' ? '❌ Ödeme Hatası' :
               '💳 Kredi Satın Al'}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              {paymentStatus === 'success' ? 'Kredileriniz hesabınıza eklendi.' :
               paymentStatus === 'canceled' ? 'İşleminiz iptal edildi.' :
               paymentStatus === 'error' ? 'Bir hata oluştu, tekrar deneyin.' :
               'İhtiyacın olan krediyi seç, hemen kullanmaya başla'}
            </Typography>
          </Box>
          {paymentStatus === 'idle' && (
            <IconButton onClick={handleClose} size="small" sx={{ color: 'white' }}>
              <Close />
            </IconButton>
          )}
        </Box>
        {paymentStatus === 'idle' && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={`💰 Mevcut: ${currentBalance} Kredi`} 
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'white',
                fontWeight: 'bold',
              }} 
            />
          </Box>
        )}
      </Box>

      <DialogContent sx={{ p: 3, bgcolor: '#f8f9fa' }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading && paymentStatus === 'idle' ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          renderContent()
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, bgcolor: '#f8f9fa', borderTop: '1px solid #e0e0e0' }}>
        {renderActions()}
      </DialogActions>
    </Dialog>
  );
}