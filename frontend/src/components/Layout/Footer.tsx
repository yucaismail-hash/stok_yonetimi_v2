import { Box, Typography, Link, Container, Chip, Stack, IconButton, Tooltip } from '@mui/material';
import { GitBranch, Circle, BookOpen, Cloud, ShieldCheck } from 'lucide-react';
import { GitHub, LinkedIn } from '@mui/icons-material'; // ✅ MUI Icons

export default function Footer() {
  const currentYear = new Date().getFullYear();
  const currentMonth = String(new Date().getMonth() + 1).padStart(2, '0');

  return (
    <Box
      component="footer"
      sx={{
        mt: 4,
        py: 3,
        borderTop: '1px solid #e8f0fe',
        backgroundColor: '#fafcff',
      }}
    >
      <Container maxWidth="lg">
        {/* Ana Grid - 3 Sütunlu */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 2fr 1fr' },
            gap: { xs: 3, md: 2 },
            alignItems: 'center',
          }}
        >
          {/* Sol - Marka ve Versiyon */}
          <Box>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: '#1f4e79',
                  letterSpacing: '-0.5px',
                  fontSize: '1rem',
                }}
              >
                Stokonomi
              </Typography>
              <Chip
                icon={<GitBranch size={12} />}
                label="v1.0.0"
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.55rem',
                  fontWeight: 500,
                  backgroundColor: '#f0f7ff',
                  color: '#1f4e79',
                  '& .MuiChip-icon': {
                    color: '#1f4e79',
                  },
                }}
              />
            </Stack>
            <Typography
              variant="caption"
              sx={{
                color: '#9e9e9e',
                fontSize: '0.65rem',
                fontWeight: 400,
                display: 'block',
                mt: 0.5,
              }}
            >
              AI Inventory Platform
            </Typography>
          </Box>

          {/* Orta - Linkler ve Copyright */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: { xs: 'flex-start', md: 'center' },
              gap: 1,
            }}
          >
            {/* Ana Linkler */}
            <Stack
              direction="row"
              spacing={2.5}
              sx={{
                alignItems: 'center',
                flexWrap: 'wrap',
                justifyContent: { xs: 'flex-start', md: 'center' },
              }}
            >
              <Link
                href="#"
                variant="body2"
                sx={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#1f4e79',
                  },
                }}
              >
                Gizlilik
              </Link>
              <Link
                href="#"
                variant="body2"
                sx={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#1f4e79',
                  },
                }}
              >
                Şartlar
              </Link>
              <Link
                href="#"
                variant="body2"
                sx={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#1f4e79',
                  },
                }}
              >
                Destek
              </Link>
              <Link
                href="#"
                variant="body2"
                sx={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#1f4e79',
                  },
                }}
              >
                API
              </Link>
              <Link
                href="#"
                variant="body2"
                sx={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#1f4e79',
                  },
                }}
              >
                Dokümantasyon
              </Link>
            </Stack>

            {/* Sosyal Medya ve Copyright */}
            <Stack
              direction="row"
              spacing={2}
              sx={{
                alignItems: 'center',
                flexWrap: 'wrap',
                justifyContent: { xs: 'flex-start', md: 'center' },
              }}
            >
              {/* Sosyal Medya İkonları - MUI Icons */}
              <Stack
                direction="row"
                spacing={1}
                sx={{
                  alignItems: 'center',
                }}
              >
                <Tooltip title="GitHub" arrow>
                  <IconButton
                    size="small"
                    href="#"
                    sx={{
                      color: '#9e9e9e',
                      '&:hover': {
                        color: '#1f4e79',
                        backgroundColor: '#f0f7ff',
                      },
                    }}
                  >
                    <GitHub fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="LinkedIn" arrow>
                  <IconButton
                    size="small"
                    href="#"
                    sx={{
                      color: '#9e9e9e',
                      '&:hover': {
                        color: '#1f4e79',
                        backgroundColor: '#f0f7ff',
                      },
                    }}
                  >
                    <LinkedIn fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Dokümantasyon" arrow>
                  <IconButton
                    size="small"
                    href="#"
                    sx={{
                      color: '#9e9e9e',
                      '&:hover': {
                        color: '#1f4e79',
                        backgroundColor: '#f0f7ff',
                      },
                    }}
                  >
                    <BookOpen size={16} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="API Durumu" arrow>
                  <IconButton
                    size="small"
                    href="#"
                    sx={{
                      color: '#9e9e9e',
                      '&:hover': {
                        color: '#1f4e79',
                        backgroundColor: '#f0f7ff',
                      },
                    }}
                  >
                    <Cloud size={16} />
                  </IconButton>
                </Tooltip>
              </Stack>

              <Box
                sx={{
                  width: 1,
                  height: 14,
                  backgroundColor: '#e0e0e0',
                  display: { xs: 'none', sm: 'block' },
                }}
              />

              <Typography
                variant="caption"
                sx={{
                  color: '#b0b0b0',
                  fontSize: '0.6rem',
                  fontWeight: 400,
                }}
              >
                © {currentYear} Stokonomi
              </Typography>
            </Stack>
          </Box>

          {/* Sağ - Sistem Durumu */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: { xs: 'flex-start', md: 'flex-end' },
              gap: 0.5,
            }}
          >
            <Stack
              direction="row"
              spacing={1.5}
              sx={{
                alignItems: 'center',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  backgroundColor: '#f0fdf4',
                  px: 1.5,
                  py: 0.5,
                  borderRadius: 20,
                  border: '1px solid #bbf7d0',
                }}
              >
                <Circle
                  size={8}
                  fill="#22c55e"
                  stroke="#22c55e"
                  strokeWidth={0}
                />
                <Typography
                  variant="caption"
                  sx={{
                    color: '#16a34a',
                    fontWeight: 600,
                    fontSize: '0.65rem',
                    letterSpacing: '0.3px',
                  }}
                >
                  Operational
                </Typography>
              </Box>
            </Stack>

            <Stack
              direction="row"
              spacing={1.5}
              sx={{
                alignItems: 'center',
              }}
            >
              <ShieldCheck size={12} color="#6b7280" />
              <Typography
                variant="caption"
                sx={{
                  color: '#9e9e9e',
                  fontSize: '0.55rem',
                  fontWeight: 400,
                }}
              >
                Release {currentYear}.{currentMonth}
              </Typography>
            </Stack>
          </Box>
        </Box>

        {/* Alt Bilgi - Sadece Mobil İçin */}
        <Box
          sx={{
            display: { xs: 'block', md: 'none' },
            textAlign: 'center',
            mt: 2,
            pt: 2,
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: '#b0b0b0',
              fontSize: '0.55rem',
              fontWeight: 400,
            }}
          >
            © {currentYear} Stokonomi. Tüm hakları saklıdır.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}