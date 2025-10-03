import { createContext, useState } from 'react';
import { Alert, Snackbar } from '@mui/material';

export const AlertContext = createContext();

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);

  const addAlert = (messageOrObject, type = 'info', duration = 5000) => {
    let message, alertType, alertDuration;
    
    if (typeof messageOrObject === 'object' && messageOrObject !== null) {
      // Handle object parameter (backward compatibility)
      message = messageOrObject.message;
      alertType = messageOrObject.type || 'info';
      alertDuration = messageOrObject.duration || 5000;
    } else {
      // Handle individual parameters
      message = messageOrObject;
      alertType = type;
      alertDuration = duration;
    }
    
    const alert = {
      id: Date.now() + Math.random(),
      message,
      type: alertType,
      duration: alertDuration,
    };
    
    setAlerts(prev => [...prev, alert]);
    
    if (alertDuration > 0) { // Fixed: was finalDuration
      setTimeout(() => {
        removeAlert(alert.id);
      }, alertDuration); // Fixed: was finalDuration
    }
    
    return alert.id;
  };

  const removeAlert = (id) => {
    setAlerts((prevAlerts) => prevAlerts.filter((alert) => alert.id !== id));
  };

  const success = (message, autoHideDuration) => {
    return addAlert(message, 'success', autoHideDuration);
  };

  const error = (message, autoHideDuration) => {
    return addAlert(message, 'error', autoHideDuration);
  };

  const warning = (message, autoHideDuration) => {
    return addAlert(message, 'warning', autoHideDuration);
  };

  const info = (message, autoHideDuration) => {
    return addAlert(message, 'info', autoHideDuration);
  };

  const value = {
    addAlert,
    removeAlert,
    success,
    error,
    warning,
    info,
  };

  return (
    <AlertContext.Provider value={value}>
      {children}
      {alerts.map((alert) => (
        <Snackbar
          key={alert.id}
          open
          autoHideDuration={alert.duration}
          onClose={() => removeAlert(alert.id)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert severity={alert.type} onClose={() => removeAlert(alert.id)}>
            {alert.message}
          </Alert>
        </Snackbar>
      ))}
    </AlertContext.Provider>
  );
};