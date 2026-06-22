import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, CircularProgress } from '@mui/material';
import { useState } from 'react';
import * as XLSX from 'xlsx';

interface FileUploaderProps {
  onDataExtracted: (data: any[], columns: string[]) => void;
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
    setLoading(true);
    try {
      const data = await readExcel(file);
      const columns = Object.keys(data[0] || {});
      onDataExtracted(data, columns);
    } catch (error) {
      console.error('Dosya okuma hatası', error);
    } finally {
      setLoading(false);
    }
  };

  const readExcel = (file: File): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const data = e.target?.result;
        const workbook = XLSX.read(data, { type: 'binary' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(worksheet);
        resolve(json);
      };
      reader.onerror = reject;
      reader.readAsBinaryString(file);
    });
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