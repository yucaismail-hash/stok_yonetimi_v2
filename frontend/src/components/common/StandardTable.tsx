// frontend/src/components/common/StandardTable.tsx
// Stokonomi Design System - Standard Table

import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Typography,
  Chip,
  Tooltip,
} from '@mui/material';
import { ReactNode } from 'react';

export interface TableColumn {
  id: string;
  label: string;
  align?: 'left' | 'center' | 'right';
  width?: number | string;
  sticky?: boolean;
  highlight?: boolean;
  render?: (value: any, row: any) => ReactNode;
}

interface StandardTableProps {
  columns: TableColumn[];
  rows: any[];
  rowKey: string;
  loading?: boolean;
  emptyMessage?: string;
  page: number;
  rowsPerPage: number;
  onPageChange: (event: unknown, newPage: number) => void;
  onRowsPerPageChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  totalCount: number;
  rowsPerPageOptions?: number[];
  stickyHeader?: boolean;
  highlightAIColumns?: boolean;
}

export default function StandardTable({
  columns,
  rows,
  rowKey,
  loading = false,
  emptyMessage = 'Veri bulunamadı.',
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange,
  totalCount,
  rowsPerPageOptions = [25, 50, 100, 200],
  stickyHeader = true,
  highlightAIColumns = false,
}: StandardTableProps) {
  const paginatedRows = rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  // AI kolon ID'leri (highlight için)
  const aiColumnIds = ['ai_decision', 'recommended_method', 'recommended_ss', 'recommended_rop', 'risk', 'confidence'];

  return (
    <Paper sx={{ borderRadius: 2, border: '1px solid #e8f0fe', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 'calc(100vh - 300px)' }}>
        <Table stickyHeader={stickyHeader} size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f0f7ff' }}>
              {columns.map((col) => (
                <TableCell
                  key={col.id}
                  align={col.align || 'left'}
                  sx={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    color: '#1f4e79',
                    whiteSpace: 'nowrap',
                    width: col.width || 'auto',
                    position: col.sticky ? 'sticky' : 'relative',
                    left: col.sticky ? 0 : 'auto',
                    zIndex: col.sticky ? 10 : 1,
                    bgcolor: highlightAIColumns && aiColumnIds.includes(col.id) ? '#f0f7ff' : '#f8faff',
                    borderBottom: '2px solid #e0e8f0',
                    padding: '6px 12px',
                    minWidth: col.highlight ? 100 : 'auto',
                  }}
                >
                  {col.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">Yükleniyor...</Typography>
                </TableCell>
              </TableRow>
            ) : paginatedRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{emptyMessage}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedRows.map((row) => (
                <TableRow
                  key={row[rowKey] || row.id}
                  hover
                  sx={{
                    '&:hover': { bgcolor: '#f8faff' },
                    '& td': {
                      padding: '6px 12px',
                      fontSize: '0.65rem',
                      height: 42,
                    },
                  }}
                >
                  {columns.map((col) => {
                    const value = row[col.id];
                    const isAI = highlightAIColumns && aiColumnIds.includes(col.id);

                    return (
                      <TableCell
                        key={col.id}
                        align={col.align || 'left'}
                        sx={{
                          position: col.sticky ? 'sticky' : 'relative',
                          left: col.sticky ? 0 : 'auto',
                          zIndex: col.sticky ? 5 : 1,
                          bgcolor: col.sticky ? (isAI ? '#f0f7ff' : 'white') : 'inherit',
                          fontWeight: isAI ? 500 : 400,
                          borderBottom: '1px solid #f0f0f0',
                          minWidth: col.width || 'auto',
                        }}
                      >
                        {col.render ? col.render(value, row) : value ?? '-'}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={rowsPerPageOptions}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={onPageChange}
        onRowsPerPageChange={onRowsPerPageChange}
        labelRowsPerPage="Satır:"
        sx={{
          borderTop: '1px solid #f0f0f0',
          '& .MuiTablePagination-select': { fontSize: '0.7rem' },
          '& .MuiTablePagination-displayedRows': { fontSize: '0.7rem' },
        }}
      />
    </Paper>
  );
}