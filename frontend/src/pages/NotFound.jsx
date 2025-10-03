import { Box, Button, Container, Typography } from '@mui/material';
import { Home as HomeIcon, Search as SearchIcon } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

const NotFound = () => {
  const { theme } = useTheme();
  
  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '70vh',
          textAlign: 'center',
          py: 8,
        }}
      >
        <Typography 
          variant="h1" 
          component="h1" 
          sx={{ 
            fontSize: { xs: '6rem', md: '10rem' },
            fontWeight: 700,
            color: theme === 'dark' ? 'primary.main' : 'secondary.main',
            mb: 2,
          }}
        >
          404
        </Typography>
        
        <Typography 
          variant="h4" 
          component="h2"
          gutterBottom
          sx={{ mb: 3 }}
        >
          Page Not Found
        </Typography>
        
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ 
            maxWidth: '600px',
            mb: 6,
          }}
        >
          The page you are looking for might have been removed, had its name changed,
          or is temporarily unavailable. Please check the URL or navigate back to the homepage.
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<HomeIcon />}
            component={RouterLink}
            to="/"
          >
            Back to Home
          </Button>
          
          <Button
            variant="outlined"
            color="primary"
            size="large"
            startIcon={<SearchIcon />}
            component={RouterLink}
            to="/scan"
          >
            Scan a File
          </Button>
        </Box>
        
        {/* Security shield illustration */}
        <Box 
          sx={{ 
            mt: 8,
            opacity: 0.7,
          }}
        >
          <svg 
            width="200" 
            height="200" 
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" 
              stroke={theme === 'dark' ? '#90caf9' : '#1976d2'}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
            <path 
              d="M9 10L11 12L15 8" 
              stroke={theme === 'dark' ? '#90caf9' : '#1976d2'}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        </Box>
      </Box>
    </Container>
  );
};

export default NotFound;