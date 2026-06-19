import { Box, Typography, Link } from '@mui/material';

export default function Footer() {
  return (
    <Box sx={{ textAlign: 'center', mt: 4, py: 2, borderTop: '1px solid #ddd' }}>
      <Typography variant="body2" color="text.secondary">
        © {new Date().getFullYear()} AI Stok Yönetim Sistemi | Tüm hakları saklıdır.
        <Link href="#" sx={{ ml: 2 }}>Gizlilik Politikası</Link>
        <Link href="#" sx={{ ml: 2 }}>Kullanım Şartları</Link>
      </Typography>
    </Box>
  );
}