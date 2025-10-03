import { Box, Container, Typography, Link, Divider } from '@mui/material';
import { Security as SecurityIcon } from '@mui/icons-material';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <Box
      component="footer"
      sx={{
        py: 2,
        px: 2,
        mt: 'auto',
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        backgroundColor: (theme) =>
          theme.palette.mode === 'light'
            ? theme.palette.grey[100]
            : theme.palette.background.paper,
        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
        zIndex: (theme) => theme.zIndex.appBar - 1,
      }}
    >
      <Container maxWidth="lg" sx={{ height: '100%' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            justifyContent: 'space-between',
            alignItems: 'center',
            height: '100%',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <SecurityIcon color="primary" sx={{ mr: 1, fontSize: '1.2rem' }} />
            <Typography variant="body2" color="text.primary" sx={{ fontWeight: 500 }}>
              Trojan Defender
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
              © {currentYear}
            </Typography>
          </Box>

          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              gap: 3,
            }}
          >
            <Link
              href="#"
              color="text.secondary"
              underline="hover"
              variant="body2"
              sx={{ fontSize: '0.8rem' }}
            >
              Privacy Policy
            </Link>
            <Link
              href="#"
              color="text.secondary"
              underline="hover"
              variant="body2"
              sx={{ fontSize: '0.8rem' }}
            >
              Terms of Service
            </Link>
            <Link
              href="#"
              color="text.secondary"
              underline="hover"
              variant="body2"
              sx={{ fontSize: '0.8rem' }}
            >
              Support
            </Link>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;