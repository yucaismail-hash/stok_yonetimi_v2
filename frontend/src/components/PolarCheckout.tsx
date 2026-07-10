import { useEffect, useRef, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  CircularProgress,
  Alert,
  Typography,
  IconButton,
} from '@mui/material';
import { Close, CheckCircle } from '@mui/icons-material';

interface PolarCheckoutProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onCancel?: () => void;
  checkoutUrl: string;
  productName: string;
}

declare global {
  interface Window {
    Polar: any;
  }
}

export default function PolarCheckout({
  open,
  onClose,
  onSuccess,
  onCancel,
  checkoutUrl,
  productName,
}: PolarCheckoutProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutInstance, setCheckoutInstance] = useState<any>(null);
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const initAttemptedRef = useRef(false);

  useEffect(() => {
    if (!open || !checkoutUrl) {
      setLoading(false);
      initAttemptedRef.current = false;
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
      return;
    }

    if (!containerRef.current) {
      const checkContainer = setInterval(() => {
        if (containerRef.current) {
          clearInterval(checkContainer);
          initCheckout();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkContainer);
        if (!containerRef.current) {
          setError('Ödeme alanı bulunamadı.');
          setLoading(false);
        }
      }, 5000);

      return;
    }

    if (!initAttemptedRef.current) {
      initAttemptedRef.current = true;
      initCheckout();
    }

    return () => {
      if (checkoutInstance && checkoutInstance.close) {
        checkoutInstance.close();
      }
    };
  }, [open, checkoutUrl]);

  const initCheckout = async () => {
    try {
      if (!containerRef.current) {
        throw new Error('Container elementi bulunamadı');
      }

      if (!window.Polar?.EmbedCheckout) {
        throw new Error('Polar SDK yüklenmedi');
      }

      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }

      console.log('🔍 [DEBUG] Creating checkout with URL:', checkoutUrl);

      const checkout = await window.Polar.EmbedCheckout.create(checkoutUrl, {
        container: containerRef.current,
        theme: 'light',
        onSuccess: () => {
          console.log('🔍 [DEBUG] ====== onSuccess CALLED ======');
          setStatus('success');
          // ✅ Parent'a bildir, kapatmayı bildirim yapacak
          onSuccess();
        },
        onError: (error: any) => {
          console.error('🔍 [DEBUG] ====== onError CALLED ======');
          console.error('🔍 [DEBUG] Hata:', error);
          setError('Ödeme sırasında bir hata oluştu.');
          setStatus('error');
        },
        onLoaded: () => {
          console.log('🔍 [DEBUG] ====== onLoaded CALLED ======');
          setLoading(false);
        },
        onClose: () => {
          console.log('🔍 [DEBUG] ====== onClose CALLED ======');
          if (onCancel && status !== 'success') {
            onCancel();
          }
        },
        onConfirmed: () => {
            console.log("confirmed");

            setStatus("success");

            onSuccess();
        }
      });

      setCheckoutInstance(checkout);
      setLoading(false);
      setStatus('idle');

    } catch (err: any) {
      console.error('❌ Checkout init error:', err);
      setError(err.message || 'Ödeme sistemi başlatılamadı.');
      setLoading(false);
    }
  };

  const handleClose = () => {
    console.log('🔍 [DEBUG] handleClose called, status:', status);
    if (checkoutInstance && checkoutInstance.close) {
      checkoutInstance.close();
    }
    setCheckoutInstance(null);
    setStatus('idle');
    setError(null);
    setLoading(true);
    initAttemptedRef.current = false;

    if (containerRef.current) {
      containerRef.current.innerHTML = '';
    }

    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            height: '80vh',
            maxHeight: '80vh',
            borderRadius: 2,
            position: 'relative',
            overflow: 'hidden',
            bgcolor: '#f8f9fa',
          },
        },
      }}
    >
      <DialogTitle sx={{ bgcolor: '#fff', borderBottom: '1px solid #e0e0e0' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            💳 {productName || 'Kredi Satın Al'}
          </Typography>
          <IconButton onClick={handleClose} size="small" color="error">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, position: 'relative', overflow: 'hidden' }}>
        {loading && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              height: 400,
              gap: 2,
            }}
          >
            <CircularProgress size={40} thickness={4} />
            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              Ödeme Ekranı Hazırlanıyor
            </Typography>
          </Box>
        )}

        {error && (
          <Box
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: 400,
            }}
          >
            <Alert
              severity="error"
              sx={{ maxWidth: 400 }}
              action={
                <Button color="inherit" size="small" onClick={() => window.location.reload()}>
                  Yenile
                </Button>
              }
            >
              {error}
            </Alert>
          </Box>
        )}

        {status === 'success' && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              height: 400,
            }}
          >
            <CheckCircle sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h5" sx={{ mt: 2, fontWeight: 'bold' }}>
              🎉 Ödeme Başarılı!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Kredileriniz hesabınıza eklendi.
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={handleClose}
              sx={{ mt: 3 }}
            >
              Dashboard'a Dön
            </Button>
          </Box>
        )}

        <div
          ref={containerRef}
          style={{
            width: '0',
            height: '0',
            opacity: 0,
            pointerEvents: 'none',
            position: 'absolute',
            top: '-9999px',
            left: '-9999px',
            overflow: 'hidden',
            display: loading || error || status === 'success' ? 'none' : 'block',
          }}
        />
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: '1px solid #e0e0e0', bgcolor: '#fff' }}>
        <Button onClick={handleClose} color="inherit">
          İptal
        </Button>
      </DialogActions>
    </Dialog>
  );
}