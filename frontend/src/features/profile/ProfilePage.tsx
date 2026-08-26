import { Alert, Box, Card, CardContent, Chip, Divider, Stack, Typography } from '@mui/material';
import { useAuth } from '../../hooks/useAuth';

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return <Alert severity="error">Kullanıcı bilgisi yüklenemedi.</Alert>;
  return <Box sx={{ maxWidth: 760, mx: 'auto' }}>
    <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>Hesabım</Typography>
    <Card><CardContent><Stack spacing={2}>
      <Box><Typography variant="caption" color="text.secondary">Ad soyad</Typography><Typography>{user.full_name || 'Belirtilmemiş'}</Typography></Box><Divider />
      <Box><Typography variant="caption" color="text.secondary">E-posta</Typography><Typography>{user.email}</Typography></Box><Divider />
      <Box><Typography variant="caption" color="text.secondary">Şirket kimliği</Typography><Typography sx={{ wordBreak: 'break-all' }}>{user.company_id}</Typography></Box><Divider />
      <Box><Typography variant="caption" color="text.secondary">Rol</Typography><br /><Chip label={user.role} size="small" /></Box><Divider />
      <Box><Typography variant="caption" color="text.secondary">Dil / zaman dilimi</Typography><Typography>{user.language} · {user.timezone}</Typography></Box>
    </Stack></CardContent></Card>
    <Alert severity="info" sx={{ mt: 2 }}>Şirket, fatura ve kredi bilgileri canonical kullanıcı sözleşmesinin parçası değildir.</Alert>
  </Box>;
}
