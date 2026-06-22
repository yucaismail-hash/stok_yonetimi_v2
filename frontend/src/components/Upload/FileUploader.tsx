import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, CircularProgress } from '@mui/material';
import { useState } from 'react';
import * as XLSX from 'xlsx';

interface FileUploaderProps {
  onDataExtracted: (file: File) => void;  // ✅ Değişti: dosya nesnesi alıyor
  accept?: string;
}

export default function FileUploader({ onDataExtracted, accept = '.xlsx,.xls,.csv' }: FileUploaderProps) {
  const [loading, setLoading] = useState(false);

  // ✅ react-dropzone için doğru accept formatı
  const getAccept = () => {
    if (!accept) return undefined;
    
    const acceptMap: Record<string, string[]> = {};
    const extensions = accept.split(',').map(ext => ext.trim());
    
    extensions.forEach(ext => {
      if (ext === '.xlsx') {
        acceptMap['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = ['.xlsx'];
      } else if (ext === '.xls') {
        acceptMap['application/vnd.ms-excel'] = ['.xls'];
      } else if (ext === '.csv') {
        acceptMap['text/csv'] = ['.csv'];
      }
    });
    
    return acceptMap;
  };

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;
    
    // ✅ Doğrudan dosyayı parent'a gönder
    onDataExtracted(file);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop, 
    accept: getAccept()
  });

  return (
    <Box {...getRootProps()} sx={{ border: '2px dashed #ccc', p: 4, textAlign: 'center', cursor: 'pointer', borderRadius: 2 }}>
      <input {...getInputProps()} />
      {loading ? (
        <CircularProgress />
      ) : isDragActive ? (
        <Typography>Dosyayı buraya bırakın...</Typography>
      ) : (
        <Typography>Excel veya CSV dosyasını sürükleyin veya tıklayın</Typography>
      )}
      <Button variant="contained" sx={{ mt: 2 }}>Dosya Seç</Button>
    </Box>
  );
}