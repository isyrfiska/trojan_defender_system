/**
 * Network Monitor Component
 * Provides real-time network health monitoring and user feedback
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Alert,
  Snackbar,
  LinearProgress,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Fade,
  Chip,
  Badge
} from '@mui/material';
import {
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import networkManager from '../../services/NetworkManager';
import { useAlert } from '../../hooks/useAlert';

const NetworkMonitor = () => {
  const [networkStatus, setNetworkStatus] = useState({
    isOnline: navigator.onLine,
    health: 'unknown',
    responseTime: null,
    lastCheck: null,
    circuitBreakers: [],
    offlineQueueSize: 0
  });
  const [showDetails, setShowDetails] = useState(false);
  const [notification, setNotification] = useState(null);
  const { addAlert } = useAlert();

  /**
   * Update network status
   */
  const updateNetworkStatus = useCallback(() => {
    const health = networkManager.getNetworkHealth();
    const isHealthy = health.healthChecks.size > 0 && 
                     Array.from(health.healthChecks.values()).every(check => check.status === 'healthy');
    
    const avgResponseTime = health.healthChecks.size > 0 
      ? Array.from(health.healthChecks.values())
          .filter(check => check.responseTime)
          .reduce((sum, check) => sum + check.responseTime, 0) / health.healthChecks.size
      : null;

    setNetworkStatus({
      isOnline: health.isOnline,
      health: isHealthy ? 'healthy' : 'unhealthy',
      responseTime: avgResponseTime,
      lastCheck: health.healthChecks.size > 0 
        ? Math.max(...Array.from(health.healthChecks.values()).map(check => check.lastCheck))
        : null,
      circuitBreakers: Array.from(health.circuitBreakers.entries()),
      offlineQueueSize: health.offlineQueueSize
    });
  }, []);

  /**
   * Setup network monitoring
   */
  useEffect(() => {
    const handleOnline = () => {
      setNotification({
        message: 'Network connection restored',
        severity: 'success',
        icon: <CheckCircleIcon />
      });
      updateNetworkStatus();
    };

    const handleOffline = () => {
      setNotification({
        message: 'Network connection lost',
        severity: 'error',
        icon: <WifiOffIcon />
      });
      updateNetworkStatus();
    };

    // Initial status update
    updateNetworkStatus();

    // Setup event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Periodic status updates
    const interval = setInterval(updateNetworkStatus, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [updateNetworkStatus]);

  /**
   * Handle manual refresh
   */
  const handleRefresh = useCallback(async () => {
    try {
      setNotification({
        message: 'Checking network health...',
        severity: 'info',
        icon: <RefreshIcon />
      });

      await networkManager.performHealthChecks();
      updateNetworkStatus();

      setNotification({
        message: 'Network health check completed',
        severity: 'success',
        icon: <CheckCircleIcon />
      });
    } catch (error) {
      setNotification({
        message: 'Network health check failed',
        severity: 'error',
        icon: <ErrorIcon />
      });
    }
  }, [updateNetworkStatus]);

  /**
   * Get status icon
   */
  const getStatusIcon = () => {
    if (!networkStatus.isOnline) {
      return <WifiOffIcon color="error" />;
    }

    switch (networkStatus.health) {
      case 'healthy':
        return <WifiIcon color="success" />;
      case 'unhealthy':
        return <WarningIcon color="warning" />;
      default:
        return <WifiIcon color="disabled" />;
    }
  };

  /**
   * Get status color
   */
  const getStatusColor = () => {
    if (!networkStatus.isOnline) return 'error';
    switch (networkStatus.health) {
      case 'healthy': return 'success';
      case 'unhealthy': return 'warning';
      default: return 'default';
    }
  };

  /**
   * Format response time
   */
  const formatResponseTime = (ms) => {
    if (ms < 100) return `${ms.toFixed(0)}ms (Excellent)`;
    if (ms < 300) return `${ms.toFixed(0)}ms (Good)`;
    if (ms < 1000) return `${ms.toFixed(0)}ms (Fair)`;
    return `${ms.toFixed(0)}ms (Poor)`;
  };

  /**
   * Get circuit breaker status
   */
  const getCircuitBreakerStatus = (state) => {
    switch (state) {
      case 'CLOSED': return { color: 'success', label: 'Closed' };
      case 'OPEN': return { color: 'error', label: 'Open' };
      case 'HALF_OPEN': return { color: 'warning', label: 'Half-Open' };
      default: return { color: 'default', label: 'Unknown' };
    }
  };

  return (
    <>
      {/* Network Status Indicator */}
      <Box sx={{ position: 'fixed', top: 16, right: 16, zIndex: 1300 }}>
        <Tooltip 
          title={
            <Box>
              <Typography variant="body2">
                Network Status: {networkStatus.isOnline ? 'Online' : 'Offline'}
              </Typography>
              <Typography variant="body2">
                Health: {networkStatus.health}
              </Typography>
              {networkStatus.responseTime && (
                <Typography variant="body2">
                  Avg Response Time: {formatResponseTime(networkStatus.responseTime)}
                </Typography>
              )}
              {networkStatus.offlineQueueSize > 0 && (
                <Typography variant="body2">
                  Offline Queue: {networkStatus.offlineQueueSize} items
                </Typography>
              )}
            </Box>
          }
        >
          <Badge 
            color={getStatusColor()} 
            variant="dot"
            overlap="circular"
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          >
            <IconButton 
              onClick={handleRefresh}
              size="small"
              sx={{ 
                backgroundColor: 'background.paper',
                boxShadow: 1,
                '&:hover': { backgroundColor: 'action.hover' }
              }}
            >
              {getStatusIcon()}
            </IconButton>
          </Badge>
        </Tooltip>
      </Box>

      {/* Network Status Notification */}
      <Snackbar
        open={!!notification}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        {notification && (
          <Alert 
            severity={notification.severity}
            onClose={() => setNotification(null)}
            icon={notification.icon}
            sx={{ minWidth: 300 }}
          >
            {notification.message}
          </Alert>
        )}
      </Snackbar>

      {/* Detailed Network Status (Optional) */}
      {showDetails && (
        <Fade in={showDetails}>
          <Box
            sx={{
              position: 'fixed',
              top: 80,
              right: 16,
              width: 350,
              backgroundColor: 'background.paper',
              borderRadius: 1,
              boxShadow: 3,
              p: 2,
              zIndex: 1300
            }}
          >
            <Typography variant="h6" gutterBottom>
              Network Health Status
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Circuit Breakers
              </Typography>
              {networkStatus.circuitBreakers.map(([key, breaker]) => {
                const status = getCircuitBreakerStatus(breaker.state);
                return (
                  <Box key={key} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Chip 
                      label={`${key}: ${status.label}`}
                      color={status.color}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Typography variant="caption">
                      Failures: {breaker.failures}
                    </Typography>
                  </Box>
                );
              })}
            </Box>

            {networkStatus.lastCheck && (
              <Typography variant="caption" color="text.secondary">
                Last Check: {new Date(networkStatus.lastCheck).toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </Fade>
      )}
    </>
  );
};

export default NetworkMonitor;