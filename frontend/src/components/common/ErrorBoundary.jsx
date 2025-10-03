import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const ErrorContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '400px',
  padding: theme.spacing(4),
  textAlign: 'center',
}));

const ErrorCard = styled(Card)(({ theme }) => ({
  maxWidth: 600,
  width: '100%',
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.error.main}`,
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[8],
}));

const StyledErrorIcon = styled(ErrorIcon)(({ theme }) => ({
  fontSize: '4rem',
  color: theme.palette.error.main,
  marginBottom: theme.spacing(2),
  animation: 'pulse 2s ease-in-out infinite',
  '@keyframes pulse': {
    '0%': {
      transform: 'scale(1)',
      opacity: 1,
    },
    '50%': {
      transform: 'scale(1.05)',
      opacity: 0.8,
    },
    '100%': {
      transform: 'scale(1)',
      opacity: 1,
    },
  },
}));

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
  minWidth: 120,
  transition: 'all 0.2s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
  },
}));

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  handleReload = () => {
    window.location.reload();
  };

  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    if (this.state.hasError) {
      const { title, message, showRetry = true, showHome = true } = this.props;

      return (
        <ErrorContainer>
          <ErrorCard>
            <CardContent>
              <StyledErrorIcon />
              
              <Typography variant="h4" component="h1" gutterBottom color="error">
                {title || 'Oops! Something went wrong'}
              </Typography>
              
              <Typography variant="body1" color="text.secondary" paragraph>
                {message || 'An unexpected error occurred. Please try again or contact support if the problem persists.'}
              </Typography>

              <Alert 
                severity="error" 
                sx={{ mb: 3, textAlign: 'left' }}
                icon={<BugReportIcon />}
              >
                <Typography variant="body2">
                  Error: {this.state.error?.message || 'Unknown error'}
                </Typography>
              </Alert>

              <Box sx={{ mb: 2 }}>
                {showRetry && (
                  <ActionButton
                    variant="contained"
                    color="primary"
                    startIcon={<RefreshIcon />}
                    onClick={this.handleRetry}
                  >
                    Try Again
                  </ActionButton>
                )}
                
                <ActionButton
                  variant="outlined"
                  color="primary"
                  startIcon={<RefreshIcon />}
                  onClick={this.handleReload}
                >
                  Reload Page
                </ActionButton>
                
                {showHome && (
                  <ActionButton
                    variant="outlined"
                    color="secondary"
                    startIcon={<HomeIcon />}
                    onClick={this.handleGoHome}
                  >
                    Go Home
                  </ActionButton>
                )}
              </Box>

              <Box>
                <Button
                  variant="text"
                  size="small"
                  onClick={this.toggleDetails}
                  endIcon={this.state.showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  sx={{ color: 'text.secondary' }}
                >
                  {this.state.showDetails ? 'Hide' : 'Show'} Error Details
                </Button>
                
                <Collapse in={this.state.showDetails}>
                  <Box
                    sx={{
                      mt: 2,
                      p: 2,
                      backgroundColor: 'grey.900',
                      borderRadius: 1,
                      textAlign: 'left',
                      maxHeight: 200,
                      overflow: 'auto',
                    }}
                  >
                    <Typography
                      variant="caption"
                      component="pre"
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        color: 'grey.300',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {this.state.error?.stack || 'No stack trace available'}
                    </Typography>
                  </Box>
                </Collapse>
              </Box>
            </CardContent>
          </ErrorCard>
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;