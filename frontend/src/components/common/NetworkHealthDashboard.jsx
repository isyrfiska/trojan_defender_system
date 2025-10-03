/**
 * Network Health Dashboard Component
 * Comprehensive monitoring and troubleshooting interface for network operations
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Fab
} from '@mui/material';
import {
  NetworkCheck as NetworkCheckIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import networkManager from '../../services/NetworkManager';
import { useAlert } from '../../hooks/useAlert';

const NetworkHealthDashboard = ({ open, onClose }) => {
  const [networkHealth, setNetworkHealth] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [errorLog, setErrorLog] = useState([]);
  const { addAlert } = useAlert();

  /**
   * Update network health data
   */
  const updateNetworkHealth = useCallback(async () => {
    if (!isMonitoring) return;

    try {
      const health = networkManager.getNetworkHealth();
      setNetworkHealth(health);
      
      // Update error log from network manager
      if (networkManager.errorLog) {
        setErrorLog(networkManager.errorLog.slice(-50)); // Last 50 errors
      }
    } catch (error) {
      addAlert({
        message: 'Failed to update network health data',
        severity: 'error'
      });
    }
  }, [isMonitoring, addAlert]);

  /**
   * Refresh network health
   */
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await networkManager.performHealthChecks();
      await updateNetworkHealth();
      
      addAlert({
        message: 'Network health refreshed successfully',
        severity: 'success'
      });
    } catch (error) {
      addAlert({
        message: 'Failed to refresh network health',
        severity: 'error'
      });
    } finally {
      setRefreshing(false);
    }
  }, [updateNetworkHealth, addAlert]);

  /**
   * Toggle monitoring
   */
  const handleToggleMonitoring = useCallback(() => {
    setIsMonitoring(!isMonitoring);
    addAlert({
      message: isMonitoring ? 'Network monitoring paused' : 'Network monitoring resumed',
      severity: 'info'
    });
  }, [isMonitoring, addAlert]);

  /**
   * Clear error log
   */
  const handleClearErrors = useCallback(() => {
    if (networkManager.clearErrorLog) {
      networkManager.clearErrorLog();
      setErrorLog([]);
      addAlert({
        message: 'Error log cleared',
        severity: 'info'
      });
    }
  }, [addAlert]);

  /**
   * Reset circuit breaker
   */
  const handleResetCircuitBreaker = useCallback((endpoint) => {
    if (networkManager.resetCircuitBreaker) {
      networkManager.resetCircuitBreaker(endpoint);
      updateNetworkHealth();
      addAlert({
        message: `Circuit breaker reset for ${endpoint}`,
        severity: 'success'
      });
    }
  }, [updateNetworkHealth, addAlert]);

  /**
   * Setup periodic updates
   */
  useEffect(() => {
    updateNetworkHealth();
    const interval = setInterval(updateNetworkHealth, 2000); // Update every 2 seconds
    
    return () => clearInterval(interval);
  }, [updateNetworkHealth]);

  /**
   * Get status icon
   */
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'unhealthy': return <ErrorIcon color="error" />;
      default: return <WarningIcon color="warning" />;
    }
  };

  /**
   * Get circuit breaker icon
   */
  const getCircuitBreakerIcon = (state) => {
    switch (state) {
      case 'CLOSED': return <CheckCircleIcon color="success" />;
      case 'OPEN': return <ErrorIcon color="error" />;
      case 'HALF_OPEN': return <WarningIcon color="warning" />;
      default: return <WarningIcon color="disabled" />;
    }
  };

  /**
   * Format timestamp
   */
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  /**
   * Format duration
   */
  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  if (!networkHealth) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <LinearProgress />
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <>
      {/* Floating Action Button for quick access */}
      <Fab
        color="primary"
        size="small"
        onClick={onClose}
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
      >
        <NetworkCheckIcon />
      </Fab>

      <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <NetworkCheckIcon />
            <Typography variant="h6">Network Health Dashboard</Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Tooltip title={isMonitoring ? "Pause Monitoring" : "Resume Monitoring"}>
              <IconButton onClick={handleToggleMonitoring}>
                {isMonitoring ? <PauseIcon /> : <PlayIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon className={refreshing ? 'animate-spin' : ''} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Clear Errors">
              <IconButton onClick={handleClearErrors}>
                <ClearIcon />
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose}>
              <CancelIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent dividers>
          {/* Network Status Overview */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    {networkHealth.isOnline ? 
                      <WifiIcon color="success" /> : 
                      <WifiOffIcon color="error" />
                    }
                    <Box>
                      <Typography variant="h6">
                        {networkHealth.isOnline ? 'Online' : 'Offline'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Network Status
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    {getStatusIcon(networkHealth.health)}
                    <Box>
                      <Typography variant="h6">
                        {networkHealth.health.charAt(0).toUpperCase() + networkHealth.health.slice(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Overall Health
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6">
                    {networkHealth.offlineQueueSize}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Offline Queue Items
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6">
                    {networkHealth.circuitBreakers.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Circuit Breakers
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Circuit Breakers Status */}
          {networkHealth.circuitBreakers.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Circuit Breakers
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Endpoint</TableCell>
                      <TableCell>State</TableCell>
                      <TableCell>Failures</TableCell>
                      <TableCell>Last Failure</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {networkHealth.circuitBreakers.map(([endpoint, breaker]) => (
                      <TableRow key={endpoint}>
                        <TableCell>{endpoint}</TableCell>
                        <TableCell>
                          <Chip
                            icon={getCircuitBreakerIcon(breaker.state)}
                            label={breaker.state}
                            color={breaker.state === 'CLOSED' ? 'success' : 
                                   breaker.state === 'OPEN' ? 'error' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{breaker.failures}</TableCell>
                        <TableCell>
                          {formatTimestamp(breaker.lastFailureTime)}
                        </TableCell>
                        <TableCell>
                          {breaker.state === 'OPEN' && (
                            <Button
                              size="small"
                              onClick={() => handleResetCircuitBreaker(endpoint)}
                            >
                              Reset
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Error Log */}
          {errorLog.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Recent Errors ({errorLog.length})
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Message</TableCell>
                      <TableCell>Context</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {errorLog.slice(-10).reverse().map((error, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          {formatTimestamp(error.timestamp)}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={error.type}
                            color={error.severity === 'critical' ? 'error' :
                                   error.severity === 'high' ? 'warning' : 'info'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{error.message}</TableCell>
                        <TableCell>
                          {error.context && JSON.stringify(error.context).substring(0, 50)}...
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {errorLog.length === 0 && (
            <Alert severity="success" icon={<CheckCircleIcon />}>
              No network errors detected. System is operating normally.
            </Alert>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={onClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default NetworkHealthDashboard;