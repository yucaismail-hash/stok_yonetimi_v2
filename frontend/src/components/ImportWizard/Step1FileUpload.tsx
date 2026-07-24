// frontend/src/components/ImportWizard/Step1FileUpload.tsx
import { useState } from 'react';
import { Box, Typography, Paper, Button, CircularProgress, Alert, Chip } from '@mui/material';
import { CloudUpload, FilePresent } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';




interface Step1FileUploadProps {
  file: File | null;
  onFileSelect: (file: File) => void;
  loading: boolean;
  error: string | null;
}

export default function Step1FileUpload({ file, onFileSelect, loading, error }: Step1FileUploadProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    maxFiles: 1,
    disabled: loading,
  });

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Excel dosyasını sürükleyin veya tıklayarak seçin.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => {}}>
          {error}
        </Alert>
      )}

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: `2px dashed ${isDragActive ? '#1f4e79' : '#d0d0d0'}`,
          borderRadius: 2,
          bgcolor: isDragActive ? '#f0f7ff' : '#fafafa',
          cursor: loading ? 'default' : 'pointer',
          transition: 'all 0.3s',
          '&:hover': {
            bgcolor: '#f0f7ff',
            borderColor: '#1f4e79',
          },
        }}
      >
        <input {...getInputProps()} />
        {loading ? (
          <CircularProgress size={48} />
        ) : file ? (
          <Box>
            <FilePresent sx={{ fontSize: 48, color: '#1f4e79' }} />
            <Typography variant="body1" sx={{ fontWeight: 500, mt: 1 }}>
              {file.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {(file.size / 1024).toFixed(2)} KB
            </Typography>
            <Button size="small" sx={{ mt: 1, fontSize: '0.7rem' }} onClick={(e) => e.stopPropagation()}>
              Değiştir
            </Button>
          </Box>
        ) : (
          <Box>
            <CloudUpload sx={{ fontSize: 48, color: '#1f4e79' }} />
            <Typography variant="body1" sx={{ fontWeight: 500, mt: 1 }}>
              {isDragActive ? 'Dosyayı bırakın' : 'Dosya seçin veya sürükleyin'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              .xlsx, .xls - Maksimum 50 MB
            </Typography>
          </Box>
        )}
      </Paper>

      <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
        <Chip label="📊 Excel dosyası" size="small" variant="outlined" />
        <Chip label="📋 3 sheet kontrol" size="small" variant="outlined" />
        <Chip label="🔍 Akıllı doğrulama" size="small" variant="outlined" />
      </Box>
    </Box>
  );
}