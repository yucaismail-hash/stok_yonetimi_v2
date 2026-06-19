import { Card, CardContent, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material';

export default function RecentActivity() {
  const activities = [
    { id: 1, action: 'Pattern Analizi', date: '2026-06-15', tokens: 2, status: 'success' },
    { id: 2, action: 'Safety Stock', date: '2026-06-15', tokens: 3, status: 'success' },
    { id: 3, action: 'Forecast', date: '2026-06-14', tokens: 5, status: 'warning' },
    { id: 4, action: 'Backtest', date: '2026-06-14', tokens: 15, status: 'info' },
  ];

  const getChipColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Son Aktiviteler</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>İşlem</TableCell>
                <TableCell>Tarih</TableCell>
                <TableCell align="right">Token Harcama</TableCell>
                <TableCell align="right">Durum</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activities.map((act) => (
                <TableRow key={act.id}>
                  <TableCell>{act.action}</TableCell>
                  <TableCell>{act.date}</TableCell>
                  <TableCell align="right">{act.tokens}</TableCell>
                  <TableCell align="right">
                    <Chip label="Başarılı" size="small" color={getChipColor(act.status)} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}