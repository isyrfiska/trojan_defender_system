import { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  LinearProgress,
  useTheme,
  Fade,
  Grow,
  Slide,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  UploadFile,
  History,
  Public,
  Chat,
  Warning,
  Security,
  CheckCircle,
  Error as ErrorIcon,
  ArrowForward,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import useWebSocket from '../hooks/useWebSocket';
import { 
  LoadingSpinner, 
  Breadcrumbs, 
  Tooltip, 
  ErrorBoundary,
  DashboardSkeleton 
} from '../components/common';
import dashboardService from '../services/dashboardService';

const Dashboard = () => {
  const theme = useTheme();
  const { currentUser } = useAuth();
  const { connected, threatEvents, threatStats: wsThreatstats, recentThreats } = useWebSocket();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [threatStats, setThreatStats] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Use WebSocket threat stats if available, otherwise use API data
  const displayThreatStats = wsThreatstats || threatStats;

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await dashboardService.getDashboardStats();
      
      setStats({
        totalScans: data.scanStats?.total_scans || 0,
        threatsDetected: data.scanStats?.threats_detected || 0,
        cleanFiles: data.scanStats?.clean_files || 0,
        scanningSpeed: data.scanStats?.avg_scan_speed || 'N/A',
      });
      
      setRecentScans(data.recentScans || []);
      
      // Only set threat stats from API if WebSocket hasn't provided them
      if (!wsThreatstats) {
        setThreatStats(data.threatStats || null);
      }
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError(error.message || 'Failed to load dashboard data');
      
      // Fallback to empty data instead of mock data
      setStats({
        totalScans: 0,
        threatsDetected: 0,
        cleanFiles: 0,
        scanningSpeed: 'N/A',
      });
      setRecentScans([]);
      
      if (!wsThreatstats) {
        setThreatStats(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Update threat stats when WebSocket provides new data
  useEffect(() => {
    if (wsThreatstats) {
      setThreatStats(wsThreatstats);
    }
  }, [wsThreatstats]);

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    fetchDashboardData();
  };

  const handleCloseError = () => {
    setError(null);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Breadcrumbs 
          items={[
            { label: 'Home', path: '/' },
            { label: 'Dashboard', path: '/dashboard' }
          ]} 
        />
        <DashboardSkeleton />
      </Container>
    );
  }

  return (
    <ErrorBoundary title="Dashboard Error" message="Unable to load your security dashboard. Please try refreshing the page.">
      <Container maxWidth="lg">
        <Breadcrumbs />
        
        {error && (
          <Snackbar 
            open={!!error} 
            autoHideDuration={6000} 
            onClose={handleCloseError}
            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
          >
            <Alert 
              onClose={handleCloseError} 
              severity="error" 
              action={
                <Button color="inherit" size="small" onClick={handleRetry}>
                  Retry
                </Button>
              }
            >
              {error}
            </Alert>
          </Snackbar>
        )}
        
        <Fade in timeout={600}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" gutterBottom>
              Welcome back, {currentUser?.first_name || currentUser?.username || 'User'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Here's an overview of your security status and recent activities.
            </Typography>
          </Box>
        </Fade>

        {/* Quick Actions */}
        <Grow in timeout={800}>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={3}>
              <Tooltip title="Upload and scan files for malware and threats" placement="top">
                <Button
                  component={RouterLink}
                  to="/scan"
                  variant="contained"
                  fullWidth
                  startIcon={<UploadFile />}
                  sx={{ py: 2 }}
                >
                  Scan Files
                </Button>
              </Tooltip>
            </Grid>
            <Grid item xs={12} md={3}>
              <Tooltip title="View your previous scan results and history" placement="top">
                <Button
                  component={RouterLink}
                  to="/scan-history"
                  variant="outlined"
                  fullWidth
                  startIcon={<History />}
                  sx={{ py: 2 }}
                >
                  Scan History
                </Button>
              </Tooltip>
            </Grid>
            <Grid item xs={12} md={3}>
              <Tooltip title="Explore global threat intelligence and patterns" placement="top">
                <Button
                  component={RouterLink}
                  to="/threat-map"
                  variant="outlined"
                  fullWidth
                  startIcon={<Public />}
                  sx={{ py: 2 }}
                >
                  Threat Map
                </Button>
              </Tooltip>
            </Grid>
            <Grid item xs={12} md={3}>
              <Tooltip title="Get AI-powered security assistance and advice" placement="top">
                <Button
                  component={RouterLink}
                  to="/security-chat"
                  variant="outlined"
                  fullWidth
                  startIcon={<Chat />}
                  sx={{ py: 2 }}
                >
                  Security Chat
                </Button>
              </Tooltip>
            </Grid>
          </Grid>
        </Grow>

      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              borderTop: '4px solid',
              borderColor: 'primary.main',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Total Scans
            </Typography>
            <Typography
              component="p"
              variant="h3"
              sx={{ flexGrow: 1, fontWeight: 'medium' }}
            >
              {stats?.totalScans || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last 30 days
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              borderTop: '4px solid',
              borderColor: 'error.main',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Threats Detected
            </Typography>
            <Typography
              component="p"
              variant="h3"
              color="error.main"
              sx={{ flexGrow: 1, fontWeight: 'medium' }}
            >
              {stats?.threatsDetected || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {stats?.totalScans > 0 
                ? `${((stats.threatsDetected / stats.totalScans) * 100).toFixed(1)}% of total scans`
                : 'No scans yet'
              }
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              borderTop: '4px solid',
              borderColor: 'success.main',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Clean Files
            </Typography>
            <Typography
              component="p"
              variant="h3"
              color="success.main"
              sx={{ flexGrow: 1, fontWeight: 'medium' }}
            >
              {stats?.cleanFiles || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {stats?.totalScans > 0 
                ? `${((stats.cleanFiles / stats.totalScans) * 100).toFixed(1)}% of total scans`
                : 'No scans yet'
              }
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              borderTop: '4px solid',
              borderColor: 'info.main',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Scanning Speed
            </Typography>
            <Typography
              component="p"
              variant="h3"
              sx={{ flexGrow: 1, fontWeight: 'medium' }}
            >
              {stats?.scanningSpeed || 'N/A'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Average processing rate
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Scans and Threat Stats */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Recent Scans</Typography>
              <Button
                component={RouterLink}
                to="/scan-history"
                size="small"
                endIcon={<ArrowForward />}
              >
                View All
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {recentScans.length > 0 ? (
              <List>
                {recentScans.map((scan) => (
                  <ListItem
                    key={scan.id}
                    component={RouterLink}
                    to={`/scan-result/${scan.id}`}
                    sx={{
                      borderLeft: '4px solid',
                      borderColor:
                        scan.status === 'clean' ? 'success.main' : 'error.main',
                      mb: 1,
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemIcon>
                      {scan.status === 'clean' ? (
                        <CheckCircle color="success" />
                      ) : (
                        <ErrorIcon color="error" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={scan.fileName}
                      secondary={
                        <>
                          {new Date(scan.date).toLocaleString()} • {scan.fileSize}
                          {scan.status === 'threat' && (
                            <Typography
                              component="span"
                              variant="body2"
                              color="error"
                              sx={{ display: 'block' }}
                            >
                              Threat: {scan.threatName}
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No recent scans found. Start by scanning a file.
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={5}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Threat Intelligence
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Threats by Type
              </Typography>
              {displayThreatStats?.byType && displayThreatStats.byType.length > 0 ? (
                displayThreatStats.byType.map((item) => (
                  <Box key={item.type} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">{item.type}</Typography>
                      <Typography variant="body2">{item.count}</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={
                        (item.count /
                          displayThreatStats.byType.reduce((acc, curr) => acc + curr.count, 0)) *
                        100
                      }
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  {connected ? 'Loading threat data...' : 'No threat data available'}
                </Typography>
              )}
            </Box>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Threats by Region
              </Typography>
              {displayThreatStats?.byRegion && displayThreatStats.byRegion.length > 0 ? (
                displayThreatStats.byRegion.map((item) => (
                  <Box key={item.region} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">{item.region}</Typography>
                      <Typography variant="body2">{item.count}</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={
                        (item.count /
                          displayThreatStats.byRegion.reduce((acc, curr) => acc + curr.count, 0)) *
                        100
                      }
                      color="secondary"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  {connected ? 'Loading regional threat data...' : 'No regional threat data available'}
                </Typography>
              )}
            </Box>
            {/* Recent Threats Section */}
            {recentThreats && recentThreats.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Recent Threats
                </Typography>
                <List dense>
                  {recentThreats.slice(0, 3).map((threat, index) => (
                    <ListItem key={threat.id || index} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <Warning color="error" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={threat.ip_address}
                        secondary={`${threat.country} • ${threat.threat_type}`}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Button
                component={RouterLink}
                to="/threat-map"
                variant="outlined"
                endIcon={<Public />}
                sx={{ mt: 1 }}
              >
                View Threat Map
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* WebSocket Status */}
      <Paper
        elevation={1}
        sx={{
          mt: 4,
          p: 2,
          display: 'flex',
          alignItems: 'center',
          backgroundColor: connected ? 'success.light' : 'warning.light',
        }}
      >
        <Box
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            backgroundColor: connected ? 'success.main' : 'warning.main',
            mr: 2,
          }}
        />
        <Typography variant="body2">
          {connected
            ? 'Real-time threat monitoring active'
            : 'Real-time monitoring disconnected. Reconnecting...'}
        </Typography>
      </Paper>
    </Container>
    </ErrorBoundary>
  );
};

export default Dashboard;