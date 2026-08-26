// src/features/academy/components/ArticleContent.tsx
import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  Link as MuiLink,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';
import { Section, FAQ } from '../content/types';

interface ArticleContentProps {
  sections: Section[];
}

function renderParagraphContent(section: Section) {
  const content = section.content ?? '';
  const links = section.links;

  if (!links?.length) return content;

  const parts: React.ReactNode[] = [];
  let cursor = 0;

  for (const link of links) {
    const start = content.indexOf(link.text, cursor);
    if (start === -1) return content;

    if (start > cursor) parts.push(content.slice(cursor, start));
    parts.push(
      <MuiLink
        component={RouterLink}
        to={link.href}
        key={`${link.href}-${start}`}
        sx={{ fontWeight: 600 }}
      >
        {link.text}
      </MuiLink>,
    );
    cursor = start + link.text.length;
  }

  if (cursor < content.length) parts.push(content.slice(cursor));
  return parts;
}

export default function ArticleContent({ sections }: ArticleContentProps) {
  const renderSection = (section: Section, index: number) => {
    switch (section.type) {
      case 'heading':
        return (
          <Typography
            key={index}
            variant={section.level === 2 ? 'h2' : 'h3'}
            sx={{
              fontWeight: 700,
              color: (theme) => theme.palette.text.primary,
              mt: 5,
              mb: 2,
              fontSize:
                section.level === 2
                  ? { xs: '1.5rem', md: '1.8rem' }
                  : { xs: '1.2rem', md: '1.4rem' },
              lineHeight: 1.3,
            }}
          >
            {section.content}
          </Typography>
        );

      case 'paragraph':
        return (
          <Typography
            key={index}
            variant="body1"
            sx={{
              color: (theme) => theme.palette.text.primary,
              fontSize: { xs: '0.95rem', md: '1.05rem' },
              lineHeight: 1.8,
              mb: 2,
            }}
          >
            {renderParagraphContent(section)}
          </Typography>
        );

      case 'bulletList':
        return (
          <List
            key={index}
            sx={{
              mb: 3,
              pl: 2,
              '& .MuiListItem-root': {
                display: 'list-item',
                listStyleType: 'disc',
                py: 0.5,
                pl: 1,
              },
              '& .MuiListItemText-root': {
                margin: 0,
              },
              '& .MuiListItemText-primary': {
                fontSize: '0.95rem',
                lineHeight: 1.7,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            {section.items?.map((item, i) => (
              <ListItem key={i} disablePadding>
                <ListItemText primary={item} />
              </ListItem>
            ))}
          </List>
        );

      case 'numberedList':
        return (
          <List
            key={index}
            sx={{
              mb: 3,
              pl: 2,
              '& .MuiListItem-root': {
                display: 'list-item',
                listStyleType: 'decimal',
                py: 0.5,
                pl: 1,
              },
              '& .MuiListItemText-root': {
                margin: 0,
              },
              '& .MuiListItemText-primary': {
                fontSize: '0.95rem',
                lineHeight: 1.7,
                color: (theme) => theme.palette.text.primary,
              },
            }}
          >
            {section.items?.map((item, i) => (
              <ListItem key={i} disablePadding>
                <ListItemText primary={item} />
              </ListItem>
            ))}
          </List>
        );

      case 'callout':
        return (
          <Box
            key={index}
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 2,
              bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
              borderLeft: (theme) =>
                `4px solid ${theme.palette.primary.main}`,
            }}
          >
            <Typography
              variant="body1"
              sx={{
                color: (theme) => theme.palette.text.primary,
                fontSize: { xs: '0.95rem', md: '1.05rem' },
                lineHeight: 1.8,
              }}
            >
              {section.content}
            </Typography>
          </Box>
        );

      case 'formula':
        return (
          <Box
            key={index}
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 2,
              bgcolor: (theme) => alpha(theme.palette.background.default, 0.5),
              border: (theme) => `1px solid ${theme.palette.divider}`,
              textAlign: 'center',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                color: (theme) => theme.palette.text.primary,
                fontFamily: 'monospace',
                fontSize: { xs: '1rem', md: '1.2rem' },
              }}
            >
              {section.content}
            </Typography>
          </Box>
        );

      case 'example':
        return (
          <Box
            key={index}
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 2,
              bgcolor: (theme) => alpha(theme.palette.success.main, 0.03),
              border: (theme) =>
                `1px solid ${alpha(theme.palette.success.main, 0.15)}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                color: (theme) => theme.palette.success.main,
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                mb: 1,
              }}
            >
              Örnek
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: (theme) => theme.palette.text.primary,
                fontSize: { xs: '0.95rem', md: '1.05rem' },
                lineHeight: 1.8,
              }}
            >
              {section.content}
            </Typography>
          </Box>
        );

      case 'table':
        return (
          <TableContainer
            key={index}
            component={Paper}
            elevation={0}
            sx={{
              mb: 3,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <Table>
              <TableHead
                sx={{
                  bgcolor: (theme) => theme.palette.background.default,
                }}
              >
                <TableRow>
                  {section.headers?.map((header, i) => (
                    <TableCell
                      key={i}
                      sx={{
                        fontWeight: 600,
                        color: (theme) => theme.palette.text.primary,
                        borderBottom: (theme) =>
                          `1px solid ${theme.palette.divider}`,
                      }}
                    >
                      {header}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {section.rows?.map((row, i) => (
                  <TableRow key={i}>
                    {row.map((cell, j) => (
                      <TableCell
                        key={j}
                        sx={{
                          color: (theme) => theme.palette.text.primary,
                          borderBottom: (theme) =>
                            i < (section.rows?.length || 0) - 1
                              ? `1px solid ${theme.palette.divider}`
                              : 'none',
                        }}
                      >
                        {cell}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        );

      case 'faq':
        return (
          <Box key={index} sx={{ mb: 4 }}>
            <Typography
              variant="h2"
              sx={{
                fontWeight: 700,
                color: (theme) => theme.palette.text.primary,
                mt: 5,
                mb: 3,
                fontSize: { xs: '1.5rem', md: '1.8rem' },
              }}
            >
              Sık Sorulan Sorular
            </Typography>
            {section.faqs?.map((faq, i) => (
              <Box
                key={i}
                sx={{
                  py: 2,
                  borderBottom:
                    i < (section.faqs?.length || 0) - 1
                      ? (theme) => `1px solid ${theme.palette.divider}`
                      : 'none',
                }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    color: (theme) => theme.palette.text.primary,
                    fontSize: { xs: '1rem', md: '1.1rem' },
                    mb: 1,
                  }}
                >
                  {faq.question}
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: (theme) => theme.palette.text.secondary,
                    fontSize: { xs: '0.95rem', md: '1.05rem' },
                    lineHeight: 1.7,
                  }}
                >
                  {faq.answer}
                </Typography>
              </Box>
            ))}
          </Box>
        );

      case 'divider':
        return <Divider key={index} sx={{ my: 4 }} />;

      default:
        return null;
    }
  };

  return <Box>{sections.map((section, index) => renderSection(section, index))}</Box>;
}
