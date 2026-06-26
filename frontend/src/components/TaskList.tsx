import { useState, useEffect } from 'react';
import {
  Box,
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
  Typography,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Delete, Refresh, CheckCircle, Error, Pending, Visibility } from '@mui/icons-material';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

interface Task {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  total_materials: number;
  completed_materials: number;
  result_type: string;
}

interface TaskListProps {
  onViewResult: (taskId: string) => void;
}

export default function TaskList({ onViewResult }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { fetchUser } = useAuth();

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
    } catch (err) {
      console.error('Silme hatası:', err);
    }
  };

  const getStatusChip = (status: string, progress: number) => {
    switch (status) {
      case 'completed':
        return <Chip label="Tamamlandı" color="success" size="small" icon={<CheckCircle />} />;
      case 'failed':
        return <Chip label="Hata" color="error" size="small" icon={<Error />} />;
      case 'pending':
        return <Chip label="Bekliyor" color="default" size="small" icon={<Pending />} />;
      default:
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Chip label={`%${progress}`} color="primary" size="small" />
          </Box>
        );
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  useEffect(() => {
    fetchTasks();
    // ✅ Her 10 saniyede bir yenile
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Paper sx={{ p: 2, mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📋 İşlem Listesi (Async Görevler)
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" startIcon={<Refresh />} onClick={fetchTasks} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Yenile'}
          </Button>
          <Button size="small" color="error" onClick={() => setTasks([])}>
            Temizle
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {tasks.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">Henüz async görev yok</Typography>
        </Box>
      ) : (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Görev ID</TableCell>
                <TableCell>Tarih</TableCell>
                <TableCell>Durum</TableCell>
                <TableCell>İlerleme</TableCell>
                <TableCell>Malzeme</TableCell>
                <TableCell align="center">İşlem</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.task_id}>
                  <TableCell>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                      #{task.task_id.slice(0, 8)}
                    </Typography>
                  </TableCell>
                  <TableCell>{formatDate(task.created_at)}</TableCell>
                  <TableCell>{getStatusChip(task.status, task.progress)}</TableCell>
                  <TableCell sx={{ minWidth: 100 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={task.progress}
                        sx={{ flex: 1, height: 6, borderRadius: 3 }}
                      />
                      <Typography variant="caption">{task.progress}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {task.completed_materials}/{task.total_materials}
                  </TableCell>
                  <TableCell align="center">
                    {task.status === 'completed' && (
                      <Tooltip title="Sonuçları Görüntüle">
                        <IconButton size="small" onClick={() => onViewResult(task.task_id)}>
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
    </Paper>
  );
}