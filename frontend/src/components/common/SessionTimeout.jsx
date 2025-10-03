import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';

const SessionTimeout = ({
  warningTime = 5 * 60 * 1000, // 5 minutes before expiry
  sessionDuration = 30 * 60 * 1000, // 30 minutes total
}) => {
  const { isAuthenticated, logout, currentUser } = useAuth();
  const [showWarning, setShowWarning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [sessionExpired, setSessionExpired] = useState(false);

  const extendSession = useCallback(() => {
    setShowWarning(false);
    setTimeLeft(0);
    // Reset the session timer
    localStorage.setItem('lastActivity', Date.now().toString());
  }, []);

  const handleLogout = useCallback(async () => {
    setShowWarning(false);
    setSessionExpired(false);
    await logout();
  }, [logout]);

  const updateActivity = useCallback(() => {
    if (isAuthenticated) {
      localStorage.setItem('lastActivity', Date.now().toString());
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowWarning(false);
      setSessionExpired(false);
      return;
    }

    // Track user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, true);
    });

    const checkSession = () => {
      const lastActivity = localStorage.getItem('lastActivity');
      if (!lastActivity) {
        localStorage.setItem('lastActivity', Date.now().toString());
        return;
      }

      const timeSinceActivity = Date.now() - parseInt(lastActivity);
      const timeUntilExpiry = sessionDuration - timeSinceActivity;

      if (timeUntilExpiry <= 0) {
        // Session expired
        setSessionExpired(true);
        setShowWarning(false);
        setTimeout(() => {
          handleLogout();
        }, 3000); // Show expired message for 3 seconds
      } else if (timeUntilExpiry <= warningTime && !showWarning) {
        // Show warning
        setShowWarning(true);
        setTimeLeft(Math.ceil(timeUntilExpiry / 1000));
      } else if (timeUntilExpiry > warningTime && showWarning) {
        // Hide warning if user became active
        setShowWarning(false);
      }
    };

    // Check session every 30 seconds
    const interval = setInterval(checkSession, 30000);
    
    // Initial check
    checkSession();

    return () => {
      clearInterval(interval);
      events.forEach(event => {
        document.removeEventListener(event, updateActivity, true);
      });
    };
  }, [isAuthenticated, sessionDuration, warningTime, showWarning, updateActivity, handleLogout]);

  // Update countdown timer
  useEffect(() => {
    if (!showWarning || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setShowWarning(false);
          setSessionExpired(true);
          setTimeout(() => {
            handleLogout();
          }, 3000);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [showWarning, timeLeft, handleLogout]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressValue = timeLeft > 0 ? ((warningTime / 1000 - timeLeft) / (warningTime / 1000)) * 100 : 0;

  if (sessionExpired) {
    return (
      <Dialog
        open={true}
        disableEscapeKeyDown
        maxWidth="sm"
        fullWidth
      >
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <WarningIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            Session Expired
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Your session has expired due to inactivity. You will be redirected to the login page.
          </Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={showWarning}
      onClose={() => {}} // Prevent closing by clicking outside
      disableEscapeKeyDown
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TimerIcon color="warning" />
        Session Timeout Warning
      </DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }}>
          Your session will expire soon due to inactivity.
        </Alert>
        
        <Typography variant="body1" gutterBottom>
          Time remaining: <strong>{formatTime(timeLeft)}</strong>
        </Typography>
        
        <Box sx={{ mt: 2, mb: 2 }}>
          <LinearProgress 
            variant="determinate" 
            value={progressValue}
            color="warning"
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
        
        <Typography variant="body2" color="text.secondary">
          Click "Stay Logged In" to extend your session, or "Logout" to sign out now.
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleLogout} color="error">
          Logout
        </Button>
        <Button 
          onClick={extendSession} 
          variant="contained" 
          color="primary"
          autoFocus
        >
          Stay Logged In
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SessionTimeout;