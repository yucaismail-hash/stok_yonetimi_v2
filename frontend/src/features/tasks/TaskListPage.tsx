import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  LinearProgress,
  Tooltip,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Snackbar,
} from '@mui/material';
import {
  Delete,
  Refresh,
  CheckCircle,
  Error,
  Pending,
  Visibility,
  History,
  Close,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface Task {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  total_materials: number;
  completed_materials: number;
  result_type: string;
  report_name: string;
}

export default function TaskListPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/tasks/async');
      if (res.data.success) {
        setTasks(res.data.tasks || []);
      } else {
        setError('Görevler yüklenemedi');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Görevler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await api.delete(`/api/tasks/async/${taskId}`);
      fetchTasks();
      setSnackbar({
        open: true,
        message: `Görev #${taskId.slice(0,8)} başarıyla silindi.`,
        severity: 'success',
      });
    } catch (err) {
      console.error('Silme hatası:', err);
      setSnackbar({
        open: true,
        message: 'Görev silinirken bir hata oluştu.',
        severity: 'error',
      });
    }
  };

  const handleViewResult = (taskId: string, resultType: string) => {
    const pageMap: Record<string, string> = {
      'forecast_batch_async': '/forecast',
      'pattern_batch_async': '/pattern',
      'safety_stock_batch_async': '/safety-stock',
      'simulation_batch_async': '/simulation',
      'supplier_batch_async': '/supplier',
      'backtest_batch_async': '/backtest',
    };
    const path = pageMap[resultType] || '/dashboard';
    navigate(path, { state: { taskId } });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'failed':
        return <Error sx={{ color: 'error.main', fontSize: 20 }} />;
      case 'pending':
        return <Pending sx={{ color: 'warning.main', fontSize: 20 }} />;
      default:
        return <CircularProgress size={20} />;
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'completed':
        return <Chip label="Tamamlandı" color="success" size="small" />;
      case 'failed':
        return <Chip label="Hata" color="error" size="small" />;
      case 'pending':
        return <Chip label="Bekliyor" color="warning" size="small" />;
      default:
        return <Chip label="İşleniyor" color="info" size="small" />;
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  const stats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    processing: tasks.filter(t => t.status === 'processing').length,
    failed: tasks.filter(t => t.status === 'failed').length,
    pending: tasks.filter(t => t.status === 'pending').length,
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box>
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          action={
            <IconButton size="small" onClick={() => setSnackbar({ ...snackbar, open: false })}>
              <Close fontSize="small" />
            </IconButton>
          }
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Başlık */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          📋 ASYNC Görevler
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
            onClick={fetchTasks}
            disabled={loading}
          >
            {loading ? 'Yükleniyor...' : 'Yenile'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* İstatistik Kartları */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">{stats.total}</Typography>
              <Typography variant="caption" color="text.secondary">Toplam</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Card sx={{ bgcolor: 'success.light' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">{stats.completed}</Typography>
              <Typography variant="caption" color="text.secondary">Tamamlandı</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Card sx={{ bgcolor: 'info.light' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">{stats.processing}</Typography>
              <Typography variant="caption" color="text.secondary">İşleniyor</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Card sx={{ bgcolor: 'warning.light' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">{stats.pending}</Typography>
              <Typography variant="caption" color="text.secondary">Bekliyor</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 2.4 }}>
          <Card sx={{ bgcolor: 'error.light' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">{stats.failed}</Typography>
              <Typography variant="caption" color="text.secondary">Hata</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tablo */}
      {tasks.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <History sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">Henüz ASYNC görev yok</Typography>
          <Typography variant="body2" color="text.secondary">
            İlgili analiz sayfasından "ASYNC Analiz Et" butonu ile yeni bir görev başlatabilirsiniz.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main' }}>
                <TableCell sx={{ color: 'white' }}>İşlem No</TableCell>
                <TableCell sx={{ color: 'white' }}>Rapor Adı</TableCell>
                <TableCell sx={{ color: 'white' }}>Tarih</TableCell>
                <TableCell sx={{ color: 'white' }}>Durum</TableCell>
                <TableCell sx={{ color: 'white' }}>İlerleme</TableCell>
                <TableCell sx={{ color: 'white' }}>Malzeme</TableCell>
                <TableCell sx={{ color: 'white' }} align="center">İşlem</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.task_id} hover>
                  <TableCell>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                      #{task.task_id.slice(0, 8)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(task.status)}
                      <Typography variant="body2">{task.report_name}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{formatDate(task.created_at)}</TableCell>
                  <TableCell>{getStatusChip(task.status)}</TableCell>
                  <TableCell sx={{ minWidth: 120 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={task.progress}
                        sx={{ flex: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        {task.progress}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {task.completed_materials}/{task.total_materials}
                  </TableCell>
                  <TableCell align="center">
                    {task.status === 'completed' && (
                      <Tooltip title="Sonuçları Görüntüle">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleViewResult(task.task_id, task.result_type)}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Sil">
                      <IconButton size="small" color="error" onClick={() => deleteTask(task.task_id)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}