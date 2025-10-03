import { useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  Card,
  CardContent,
  CardActions,
  Stack,
  useTheme,
  Button,
} from '@mui/material';
import {
  Security,
  UploadFile,
  Public,
  Speed,
  Shield,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { GlowButton, NeonButton } from '../components/common';

const features = [
  {
    icon: <UploadFile fontSize="large" color="primary" />,
    title: 'Advanced File Scanning',
    description:
      'Upload and scan files for malware, trojans, and other threats using ClamAV and YARA rules.',
  },
  {
    icon: <Shield fontSize="large" color="primary" />,
    title: 'Comprehensive Reports',
    description:
      'Get detailed reports with threat analysis, risk assessment, and mitigation recommendations.',
  },
  {
    icon: <Public fontSize="large" color="primary" />,
    title: 'Live Threat Map',
    description:
      'Visualize global cyber threats in real-time with our interactive threat intelligence map.',
  },
  {
    icon: <Speed fontSize="large" color="primary" />,
    title: 'Real-time Alerts',
    description:
      'Receive instant notifications about detected threats via WebSockets and email alerts.',
  },
  {
    icon: <Security fontSize="large" color="primary" />,
    title: 'Secure Architecture',
    description:
      'Built with security best practices including JWT authentication, CORS, and CSP protection.',
  },
];

const Home = () => {
  const theme = useTheme();
  const { isAuthenticated, currentUser } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if user is authenticated
  useEffect(() => {
    if (isAuthenticated && currentUser) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, currentUser, navigate]);

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Hero Section */}
      <Box
        sx={{
          bgcolor: 'background.paper',
          pt: 8,
          pb: 6,
          borderRadius: 2,
          boxShadow: 1,
          mb: 4,
          background: theme.palette.mode === 'dark' 
            ? 'linear-gradient(45deg, #1a237e 30%, #311b92 90%)'
            : 'linear-gradient(45deg, #e3f2fd 30%, #bbdefb 90%)',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={7}>
              <Typography
                component="h1"
                variant="h2"
                color="text.primary"
                gutterBottom
                sx={{ fontWeight: 700 }}
              >
                Trojan Defender
              </Typography>
              <Typography
                variant="h5"
                color="text.secondary"
                paragraph
                sx={{ mb: 4 }}
              >
                Advanced malware detection and threat analysis platform.
                Protect your systems with cutting-edge scanning technology,
                real-time alerts, and comprehensive security insights.
              </Typography>
              <Stack
                direction="row"
                spacing={2}
                sx={{ justifyContent: { xs: 'center', md: 'flex-start' } }}
              >
                <GlowButton
                  size="large"
                  component={RouterLink}
                  to="/register"
                  sx={{ px: 4, py: 1.5 }}
                >
                  Get Started
                </GlowButton>
                <NeonButton
                  size="large"
                  component={RouterLink}
                  to="/login"
                  sx={{ px: 4, py: 1.5 }}
                >
                  Login
                </NeonButton>
              </Stack>
            </Grid>
            <Grid
              item
              xs={12}
              md={5}
              sx={{
                display: { xs: 'none', md: 'flex' },
                justifyContent: 'center',
              }}
            >
              <Security sx={{ fontSize: 260, opacity: 0.7, color: 'primary.main' }} />
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container sx={{ py: 8 }} maxWidth="lg">
        <Typography
          component="h2"
          variant="h3"
          align="center"
          color="text.primary"
          gutterBottom
          sx={{ mb: 6, fontWeight: 600 }}
        >
          Key Features
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item key={index} xs={12} sm={6} md={4}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 6,
                  },
                }}
                elevation={2}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'center',
                      mb: 2,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography
                    gutterBottom
                    variant="h5"
                    component="h3"
                    align="center"
                  >
                    {feature.title}
                  </Typography>
                  <Typography align="center">{feature.description}</Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                  <Button size="small" component={RouterLink} to="/register">
                    Learn More
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Call to Action */}
      <Box
        sx={{
          bgcolor: 'background.paper',
          p: 6,
          borderRadius: 2,
          boxShadow: 1,
          textAlign: 'center',
          mb: 4,
        }}
      >
        <Typography variant="h4" gutterBottom>
          Ready to secure your systems?
        </Typography>
        <Typography variant="body1" paragraph sx={{ mb: 4 }}>
          Join thousands of users who trust Trojan Defender for their security needs.
        </Typography>
        <Button
          variant="contained"
          size="large"
          component={RouterLink}
          to="/register"
          sx={{ px: 4, py: 1.5 }}
        >
          Sign Up Now
        </Button>
      </Box>
    </Box>
  );
};

export default Home;