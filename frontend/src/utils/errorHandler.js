/**
 * Enhanced Error Handler for Trojan Defender Frontend
 * Provides comprehensive error handling, logging, and user feedback
 * Integrates with NetworkManager for network error handling
 */

import { toast } from 'react-toastify';
import networkManager from '../services/NetworkManager';

// Error types for categorization
export const ERROR_TYPES = {
  NETWORK: 'NETWORK_ERROR',
  AUTHENTICATION: 'AUTH_ERROR',
  VALIDATION: 'VALIDATION_ERROR',
  PERMISSION: 'PERMISSION_ERROR',
  SERVER: 'SERVER_ERROR',
  CLIENT: 'CLIENT_ERROR',
  UNKNOWN: 'UNKNOWN_ERROR'
};

// Error severity levels
export const ERROR_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Enhanced error handler class
 */
class ErrorHandler {
  constructor() {
    this.errorLog = [];
    this.maxLogSize = 100;
    this.retryAttempts = new Map();
    this.maxRetries = 3;
  }

  /**
   * Main error handling method
   * @param {Error|Object} error - The error object
   * @param {Object} context - Additional context information
   * @param {Object} options - Handling options
   */
  handle(error, context = {}, options = {}) {
    const processedError = this.processError(error, context);
    
    // Log the error
    this.logError(processedError);
    
    // Handle based on error type and severity
    this.handleByType(processedError, options);
    
    // Show user notification if needed
    if (options.showToast !== false) {
      this.showUserNotification(processedError, options);
    }
    
    // Report to monitoring service in production
    if (import.meta.env.PROD && processedError.severity !== ERROR_SEVERITY.LOW) {
      this.reportError(processedError);
    }
    
    return processedError;
  }

  /**
   * Process and categorize the error
   * @param {Error|Object} error - Raw error
   * @param {Object} context - Context information
   */
  processError(error, context) {
    const timestamp = new Date().toISOString();
    const userAgent = navigator.userAgent;
    const url = window.location.href;
    
    let processedError = {
      id: this.generateErrorId(),
      timestamp,
      userAgent,
      url,
      context,
      originalError: error,
      message: 'An unexpected error occurred',
      type: ERROR_TYPES.UNKNOWN,
      severity: ERROR_SEVERITY.MEDIUM,
      statusCode: null,
      retryable: false,
      userMessage: 'Something went wrong. Please try again.'
    };

    // Process different error types
    if (error?.response) {
      // Axios/HTTP errors
      processedError = this.processHttpError(error, processedError);
    } else if (error?.code) {
      // Network/connection errors
      processedError = this.processNetworkError(error, processedError);
    } else if (error instanceof Error) {
      // JavaScript errors
      processedError = this.processJavaScriptError(error, processedError);
    } else if (typeof error === 'string') {
      // String errors
      processedError.message = error;
      processedError.userMessage = error;
    }

    return processedError;
  }

  /**
   * Process HTTP/API errors
   */
  processHttpError(error, processedError) {
    const { response } = error;
    processedError.statusCode = response?.status;
    processedError.message = response?.data?.message || response?.data?.detail || error.message;
    
    switch (response?.status) {
      case 400:
        processedError.type = ERROR_TYPES.VALIDATION;
        processedError.severity = ERROR_SEVERITY.LOW;
        processedError.userMessage = 'Please check your input and try again.';
        break;
      case 401:
        processedError.type = ERROR_TYPES.AUTHENTICATION;
        processedError.severity = ERROR_SEVERITY.HIGH;
        processedError.userMessage = 'Your session has expired. Please log in again.';
        break;
      case 403:
        processedError.type = ERROR_TYPES.PERMISSION;
        processedError.severity = ERROR_SEVERITY.MEDIUM;
        processedError.userMessage = 'You don\'t have permission to perform this action.';
        break;
      case 404:
        processedError.type = ERROR_TYPES.CLIENT;
        processedError.severity = ERROR_SEVERITY.LOW;
        processedError.userMessage = 'The requested resource was not found.';
        break;
      case 429:
        processedError.type = ERROR_TYPES.CLIENT;
        processedError.severity = ERROR_SEVERITY.MEDIUM;
        processedError.retryable = true;
        processedError.userMessage = 'Too many requests. Please wait a moment and try again.';
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        processedError.type = ERROR_TYPES.SERVER;
        processedError.severity = ERROR_SEVERITY.HIGH;
        processedError.retryable = true;
        processedError.userMessage = 'Server error. Please try again later.';
        break;
      default:
        processedError.type = ERROR_TYPES.UNKNOWN;
        processedError.userMessage = 'An unexpected error occurred. Please try again.';
    }

    return processedError;
  }

  /**
   * Process network errors with enhanced network manager integration
   */
  processNetworkError(error, processedError) {
    processedError.type = ERROR_TYPES.NETWORK;
    processedError.severity = ERROR_SEVERITY.HIGH;
    processedError.retryable = true;
    processedError.message = error.message || 'Network connection failed';
    processedError.userMessage = 'Connection failed. Please check your internet connection and try again.';
    
    // Add network-specific details
    if (error.code) {
      processedError.networkCode = error.code;
    }
    
    if (!navigator.onLine) {
      processedError.userMessage = 'You are offline. Some features may be limited.';
      processedError.offline = true;
    }
    
    // Integrate with network manager for circuit breaker status
    if (networkManager && error.config?.url) {
      const circuitBreaker = networkManager.getCircuitBreaker(error.config.url);
      if (circuitBreaker && circuitBreaker.state === 'OPEN') {
        processedError.circuitBreakerOpen = true;
        processedError.userMessage = 'Service temporarily unavailable. Please try again later.';
      }
    }
    
    return processedError;
  }

  /**
   * Process JavaScript errors
   */
  processJavaScriptError(error, processedError) {
    processedError.type = ERROR_TYPES.CLIENT;
    processedError.severity = ERROR_SEVERITY.MEDIUM;
    processedError.message = error.message;
    processedError.stack = error.stack;
    processedError.userMessage = 'An application error occurred. Please refresh the page and try again.';
    
    return processedError;
  }

  /**
   * Handle error based on type
   */
  handleByType(error, options) {
    switch (error.type) {
      case ERROR_TYPES.AUTHENTICATION:
        this.handleAuthError(error, options);
        break;
      case ERROR_TYPES.NETWORK:
        this.handleNetworkError(error, options);
        break;
      case ERROR_TYPES.VALIDATION:
        this.handleValidationError(error, options);
        break;
      default:
        // Default handling is already done in main handle method
        break;
    }
  }

  /**
   * Handle authentication errors
   */
  handleAuthError(error, options) {
    if (options.onAuthError) {
      options.onAuthError(error);
    } else {
      // Default: redirect to login
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    }
  }

  /**
   * Handle network errors with retry logic
   */
  handleNetworkError(error, options) {
    if (error.retryable && options.enableRetry !== false) {
      const retryKey = `${error.context?.endpoint || 'unknown'}_${error.context?.method || 'GET'}`;
      const attempts = this.retryAttempts.get(retryKey) || 0;
      
      if (attempts < this.maxRetries) {
        this.retryAttempts.set(retryKey, attempts + 1);
        
        if (options.onRetry) {
          setTimeout(() => {
            options.onRetry(attempts + 1);
          }, Math.pow(2, attempts) * 1000); // Exponential backoff
        }
      } else {
        this.retryAttempts.delete(retryKey);
      }
    }
  }

  /**
   * Handle validation errors
   */
  handleValidationError(error, options) {
    if (options.onValidationError) {
      options.onValidationError(error);
    }
  }

  /**
   * Show user notification
   */
  showUserNotification(error, options) {
    const toastOptions = {
      position: 'top-right',
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      ...options.toastOptions
    };

    switch (error.severity) {
      case ERROR_SEVERITY.CRITICAL:
      case ERROR_SEVERITY.HIGH:
        toast.error(error.userMessage, toastOptions);
        break;
      case ERROR_SEVERITY.MEDIUM:
        toast.warning(error.userMessage, toastOptions);
        break;
      case ERROR_SEVERITY.LOW:
        toast.info(error.userMessage, toastOptions);
        break;
      default:
        toast(error.userMessage, toastOptions);
    }
  }

  /**
   * Log error to internal log
   */
  logError(error) {
    this.errorLog.unshift(error);
    
    // Keep log size manageable
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }
    
    // Console logging in development
    if (import.meta.env.DEV) {
      console.group(`🚨 Error [${error.type}] - ${error.severity.toUpperCase()}`);
      console.error('Message:', error.message);
      console.error('Context:', error.context);
      console.error('Original Error:', error.originalError);
      if (error.stack) {
        console.error('Stack:', error.stack);
      }
      console.groupEnd();
    }
  }

  /**
   * Report error to monitoring service
   */
  reportError(error) {
    // In a real application, this would send to a service like Sentry, LogRocket, etc.
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: error.message,
        fatal: error.severity === ERROR_SEVERITY.CRITICAL
      });
    }
  }

  /**
   * Generate unique error ID
   */
  generateErrorId() {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get error log
   */
  getErrorLog() {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  clearErrorLog() {
    this.errorLog = [];
    this.retryAttempts.clear();
  }

  /**
   * Get error statistics
   */
  getErrorStats() {
    const stats = {
      total: this.errorLog.length,
      byType: {},
      bySeverity: {},
      recent: this.errorLog.slice(0, 10)
    };

    this.errorLog.forEach(error => {
      stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
      stats.bySeverity[error.severity] = (stats.bySeverity[error.severity] || 0) + 1;
    });

    return stats;
  }
}

// Create singleton instance
const errorHandler = new ErrorHandler();

// Convenience functions
export const handleError = (error, context, options) => errorHandler.handle(error, context, options);
export const getErrorLog = () => errorHandler.getErrorLog();
export const clearErrorLog = () => errorHandler.clearErrorLog();
export const getErrorStats = () => errorHandler.getErrorStats();

// Global error handlers
window.addEventListener('error', (event) => {
  errorHandler.handle(event.error, {
    type: 'global_error',
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno
  });
});

window.addEventListener('unhandledrejection', (event) => {
  errorHandler.handle(event.reason, {
    type: 'unhandled_promise_rejection'
  });
});

export default errorHandler;