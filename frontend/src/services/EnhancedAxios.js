/**
 * Enhanced Axios Configuration with Zero-Fault Network Operations
 * Integrates with NetworkManager for comprehensive error handling
 */

import axios from 'axios';
import networkManager from './NetworkManager';
import { handleError, ERROR_TYPES, ERROR_SEVERITY } from '../utils/errorHandler';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class EnhancedAxios {
  constructor() {
    this.instances = new Map();
    this.requestInterceptors = new Map();
    this.responseInterceptors = new Map();
    this.defaultConfig = {
      baseURL: `${API_URL}/api`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      // Enhanced configuration
      validateStatus: (status) => status >= 200 && status < 300,
      withCredentials: false,
      maxRedirects: 5,
      decompress: true,
    };
    
    this.createInstance('default', this.defaultConfig);
  }

  /**
   * Create a named axios instance with enhanced configuration
   */
  createInstance(name, config = {}) {
    const instance = axios.create({
      ...this.defaultConfig,
      ...config
    });

    // Setup comprehensive interceptors
    this.setupRequestInterceptors(instance, name);
    this.setupResponseInterceptors(instance, name);

    this.instances.set(name, instance);
    return instance;
  }

  /**
   * Setup comprehensive request interceptors
   */
  setupRequestInterceptors(instance, name) {
    // Request configuration interceptor
    const requestInterceptor = instance.interceptors.request.use(
      (config) => {
        // Add request metadata
        config.metadata = {
          startTime: Date.now(),
          instanceName: name,
          requestId: this.generateRequestId(),
          retryCount: config._retryCount || 0,
          maxRetries: config._maxRetries || 3,
          circuitBreaker: config._circuitBreaker !== false,
          offlineQueue: config._offlineQueue !== false,
        };

        // Add authentication token
        const token = localStorage.getItem('token');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }

        // Add correlation ID for distributed tracing
        config.headers['X-Correlation-ID'] = config.metadata.requestId;
        config.headers['X-Client-Version'] = import.meta.env.VITE_APP_VERSION || '1.0.0';

        // Add performance timing header
        config.headers['X-Request-Start-Time'] = config.metadata.startTime.toString();

        // Log request for debugging
        if (import.meta.env.DEV) {
          console.log(`[EnhancedAxios] ${config.method?.toUpperCase()} ${config.url}`, {
            requestId: config.metadata.requestId,
            retryCount: config.metadata.retryCount,
            timestamp: new Date().toISOString()
          });
        }

        return config;
      },
      (error) => {
        handleError(error, {
          context: 'request_interceptor',
          instanceName: name,
          stage: 'request_configuration'
        }, {
          showToast: false,
          severity: ERROR_SEVERITY.MEDIUM
        });
        return Promise.reject(error);
      }
    );

    this.requestInterceptors.set(name, requestInterceptor);
  }

  /**
   * Setup comprehensive response interceptors
   */
  setupResponseInterceptors(instance, name) {
    // Response success interceptor
    const successInterceptor = instance.interceptors.response.use(
      (response) => {
        const config = response.config;
        const metadata = config.metadata;
        
        if (metadata) {
          const endTime = Date.now();
          const duration = endTime - metadata.startTime;
          
          // Record successful response
          networkManager.recordSuccess(config.url);
          
          // Log performance metrics
          if (import.meta.env.DEV) {
            console.log(`[EnhancedAxios] ${config.method?.toUpperCase()} ${config.url} - Success (${response.status})`, {
              requestId: metadata.requestId,
              duration: `${duration}ms`,
              retryCount: metadata.retryCount,
              timestamp: new Date().toISOString()
            });
          }

          // Add performance metrics to response
          response._performance = {
            requestId: metadata.requestId,
            duration,
            startTime: metadata.startTime,
            endTime,
            retryCount: metadata.retryCount
          };
        }

        return response;
      },
      (error) => {
        return this.handleResponseError(error, name);
      }
    );

    // Response error interceptor
    const errorInterceptor = instance.interceptors.response.use(
      null,
      (error) => {
        return this.handleResponseError(error, name);
      }
    );

    this.responseInterceptors.set(name, [successInterceptor, errorInterceptor]);
  }

  /**
   * Handle response errors with comprehensive error handling
   */
  async handleResponseError(error, instanceName) {
    const config = error.config;
    const metadata = config?.metadata;
    
    if (!metadata) {
      // Handle errors without metadata (network failures, etc.)
      return this.handleNetworkError(error, instanceName);
    }

    const endTime = Date.now();
    const duration = endTime - metadata.startTime;

    // Enhanced error context
    const errorContext = {
      context: 'response_interceptor',
      instanceName,
      requestId: metadata.requestId,
      duration,
      retryCount: metadata.retryCount,
      maxRetries: metadata.maxRetries,
      url: config.url,
      method: config.method?.toUpperCase(),
      stage: 'response_handling'
    };

    // Log error for debugging
    if (import.meta.env.DEV) {
      console.error(`[EnhancedAxios] ${config.method?.toUpperCase()} ${config.url} - Error`, {
        requestId: metadata.requestId,
        status: error.response?.status,
        duration: `${duration}ms`,
        retryCount: metadata.retryCount,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }

    // Handle different error types
    if (error.response) {
      // HTTP error (status code)
      return this.handleHttpError(error, errorContext, metadata);
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      // Timeout error
      return this.handleTimeoutError(error, errorContext, metadata);
    } else if (!error.response) {
      // Network error (no response)
      return this.handleNetworkError(error, errorContext, metadata);
    } else {
      // Unknown error
      return this.handleUnknownError(error, errorContext, metadata);
    }
  }

  /**
   * Handle HTTP errors (4xx, 5xx)
   */
  async handleHttpError(error, errorContext, metadata) {
    const status = error.response.status;
    const data = error.response.data;

    // Enhanced error context
    errorContext.statusCode = status;
    errorContext.serverMessage = data?.message || data?.detail || error.message;
    errorContext.errorType = this.getHttpErrorType(status);

    // Handle specific HTTP status codes
    switch (status) {
      case 401:
        return this.handleUnauthorizedError(error, errorContext, metadata);
      case 403:
        return this.handleForbiddenError(error, errorContext, metadata);
      case 429:
        return this.handleRateLimitError(error, errorContext, metadata);
      case 408:
      case 502:
      case 503:
      case 504:
        return this.handleRetryableHttpError(error, errorContext, metadata);
      default:
        if (status >= 500) {
          return this.handleServerError(error, errorContext, metadata);
        } else {
          return this.handleClientError(error, errorContext, metadata);
        }
    }
  }

  /**
   * Handle network errors (no response)
   */
  async handleNetworkError(error, errorContext, metadata) {
    // Check if we should retry
    if (metadata.retryCount < metadata.maxRetries && this.isRetryableNetworkError(error)) {
      return this.retryRequest(error.config, errorContext, metadata);
    }

    // Record network failure
    networkManager.recordFailure(errorContext.url, error);

    // Handle offline scenario
    if (!networkManager.isOnline) {
      networkManager.queueForOffline({
        method: error.config.method,
        endpoint: error.config.url,
        data: error.config.data,
        options: error.config
      });
    }

    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.HIGH,
      userMessage: 'Network connection failed. Please check your connection and try again.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  /**
   * Handle timeout errors
   */
  async handleTimeoutError(error, errorContext, metadata) {
    if (metadata.retryCount < metadata.maxRetries) {
      return this.retryRequest(error.config, errorContext, metadata);
    }

    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.MEDIUM,
      userMessage: 'Request timed out. Please try again.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  /**
   * Handle unknown errors
   */
  async handleUnknownError(error, errorContext, metadata) {
    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.MEDIUM,
      userMessage: 'An unexpected error occurred. Please try again.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  /**
   * Handle specific HTTP error types
   */
  async handleUnauthorizedError(error, errorContext, metadata) {
    // Token refresh logic would go here
    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.HIGH,
      userMessage: 'Your session has expired. Please log in again.',
      enableRetry: false
    });

    // Redirect to login
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);

    return Promise.reject(error);
  }

  async handleForbiddenError(error, errorContext, metadata) {
    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.HIGH,
      userMessage: 'You do not have permission to perform this action.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  async handleRateLimitError(error, errorContext, metadata) {
    const retryAfter = error.response.headers['retry-after'] || 60;
    
    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.MEDIUM,
      userMessage: `Too many requests. Please try again in ${retryAfter} seconds.`,
      enableRetry: false
    });

    return Promise.reject(error);
  }

  async handleRetryableHttpError(error, errorContext, metadata) {
    if (metadata.retryCount < metadata.maxRetries) {
      return this.retryRequest(error.config, errorContext, metadata);
    }

    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.MEDIUM,
      userMessage: 'Server temporarily unavailable. Please try again later.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  async handleServerError(error, errorContext, metadata) {
    if (metadata.retryCount < metadata.maxRetries) {
      return this.retryRequest(error.config, errorContext, metadata);
    }

    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.HIGH,
      userMessage: 'Server error occurred. Our team has been notified.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  async handleClientError(error, errorContext, metadata) {
    handleError(error, errorContext, {
      showToast: true,
      severity: ERROR_SEVERITY.MEDIUM,
      userMessage: 'Invalid request. Please check your input and try again.',
      enableRetry: false
    });

    return Promise.reject(error);
  }

  /**
   * Retry request with exponential backoff
   */
  async retryRequest(config, errorContext, metadata) {
    metadata.retryCount++;
    
    const delay = Math.pow(2, metadata.retryCount) * 1000 + Math.random() * 1000;
    
    if (import.meta.env.DEV) {
      console.log(`[EnhancedAxios] Retrying request ${metadata.requestId}, attempt ${metadata.retryCount}, delay ${delay}ms`);
    }

    await this.delay(delay);

    // Update config for retry
    config._retryCount = metadata.retryCount;
    config.metadata = metadata;

    return this.instances.get(metadata.instanceName).request(config);
  }

  /**
   * Helper methods
   */
  getHttpErrorType(status) {
    if (status >= 400 && status < 500) return ERROR_TYPES.CLIENT;
    if (status >= 500) return ERROR_TYPES.SERVER;
    return ERROR_TYPES.UNKNOWN;
  }

  isRetryableNetworkError(error) {
    return !error.response && (
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('timeout') ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ENOTFOUND'
    );
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  generateRequestId() {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get instance by name
   */
  getInstance(name = 'default') {
    return this.instances.get(name);
  }

  /**
   * Get network statistics
   */
  getNetworkStats() {
    const stats = {
      instances: Array.from(this.instances.keys()),
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      networkHealth: networkManager.getNetworkHealth()
    };

    // Calculate statistics from instances
    this.instances.forEach((instance, name) => {
      // This would require tracking actual request counts
      // For now, return basic stats
    });

    return stats;
  }

  /**
   * Reset all instances and interceptors
   */
  reset() {
    this.instances.forEach((instance, name) => {
      const interceptors = this.requestInterceptors.get(name);
      const responseInterceptors = this.responseInterceptors.get(name) || [];
      
      if (interceptors) {
        instance.interceptors.request.eject(interceptors);
      }
      
      responseInterceptors.forEach(interceptor => {
        instance.interceptors.response.eject(interceptor);
      });
    });

    this.instances.clear();
    this.requestInterceptors.clear();
    this.responseInterceptors.clear();
    
    // Recreate default instance
    this.createInstance('default', this.defaultConfig);
  }
}

// Create singleton instance
const enhancedAxios = new EnhancedAxios();
export default enhancedAxios;