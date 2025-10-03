/**
 * Network Configuration for Zero-Fault Operations
 * Comprehensive network settings and constants
 */

export const NETWORK_CONFIG = {
  // Connection settings
  CONNECTION: {
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY_BASE: 1000, // 1 second
    RETRY_DELAY_MAX: 30000, // 30 seconds
    KEEP_ALIVE: true,
    WITH_CREDENTIALS: false,
  },

  // Circuit breaker settings
  CIRCUIT_BREAKER: {
    FAILURE_THRESHOLD: 5,
    RECOVERY_TIMEOUT: 60000, // 60 seconds
    HALF_OPEN_MAX_REQUESTS: 3,
    SUCCESS_THRESHOLD: 3,
  },

  // Health check settings
  HEALTH_CHECK: {
    INTERVAL: 30000, // 30 seconds
    TIMEOUT: 5000, // 5 seconds
    ENDPOINTS: [
      '/auth/token/status/',
      '/scanner/stats/',
      '/threatmap/stats/latest/',
      '/notifications/health/'
    ],
    FAILURE_THRESHOLD: 3,
    RECOVERY_THRESHOLD: 2,
  },

  // Offline mode settings
  OFFLINE_MODE: {
    QUEUE_MAX_SIZE: 100,
    CACHE_EXPIRY: 5 * 60 * 1000, // 5 minutes
    SYNC_INTERVAL: 60000, // 1 minute
    MAX_RETRY_ATTEMPTS: 3,
    FALLBACK_ENABLED: true,
  },

  // Rate limiting settings
  RATE_LIMITING: {
    MAX_REQUESTS_PER_MINUTE: 60,
    BACKOFF_MULTIPLIER: 2,
    MAX_BACKOFF_DELAY: 30000, // 30 seconds
    RETRY_AFTER_HEADER: 'retry-after',
  },

  // Error handling settings
  ERROR_HANDLING: {
    LOG_ENABLED: true,
    LOG_MAX_SIZE: 1000,
    SHOW_TOAST_NOTIFICATIONS: true,
    REPORT_TO_MONITORING: true,
    MAX_ERROR_AGE: 24 * 60 * 60 * 1000, // 24 hours
  },

  // Network quality thresholds
  NETWORK_QUALITY: {
    EXCELLENT: { rtt: 100, packetLoss: 0 },
    GOOD: { rtt: 300, packetLoss: 1 },
    FAIR: { rtt: 1000, packetLoss: 3 },
    POOR: { rtt: 3000, packetLoss: 5 },
    CRITICAL: { rtt: 5000, packetLoss: 10 },
  },

  // API endpoints configuration
  API_ENDPOINTS: {
    // Critical endpoints that require immediate attention
    CRITICAL: [
      '/auth/login/',
      '/auth/token/refresh/',
      '/auth/profile/'
    ],
    
    // Important endpoints with high availability requirements
    IMPORTANT: [
      '/scanner/stats/',
      '/scanner/results/',
      '/threatmap/stats/latest/',
      '/dashboard/data/'
    ],
    
    // Standard endpoints
    STANDARD: [
      '/scanner/upload/',
      '/notifications/',
      '/settings/',
      '/profile/'
    ],
    
    // Background endpoints with lower priority
    BACKGROUND: [
      '/analytics/',
      '/logs/',
      '/metrics/'
    ]
  },

  // Performance monitoring
  PERFORMANCE: {
    ENABLE_METRICS: true,
    SAMPLE_RATE: 0.1, // 10% of requests
    METRICS_ENDPOINT: '/metrics/network/',
    ALERT_THRESHOLD: {
      RESPONSE_TIME: 2000, // 2 seconds
      ERROR_RATE: 0.05, // 5%
      TIMEOUT_RATE: 0.02, // 2%
    },
  },

  // Security settings
  SECURITY: {
    ENABLE_CORS: true,
    ENABLE_CSRF: true,
    TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutes before expiry
    MAX_TOKEN_AGE: 24 * 60 * 60 * 1000, // 24 hours
  },

  // Browser compatibility
  BROWSER_COMPATIBILITY: {
    MIN_SUPPORTED_VERSIONS: {
      CHROME: 60,
      FIREFOX: 55,
      SAFARI: 11,
      EDGE: 79,
    },
    FEATURE_DETECTION: {
      SERVICE_WORKER: 'serviceWorker' in navigator,
      INDEXED_DB: 'indexedDB' in window,
      WEB_SOCKET: 'WebSocket' in window,
      FETCH_API: 'fetch' in window,
    },
  },

  // Fallback strategies
  FALLBACK_STRATEGIES: {
    // When primary API fails
    API_FAILURE: {
      ENABLE_CACHE_FALLBACK: true,
      ENABLE_OFFLINE_MODE: true,
      SHOW_USER_NOTIFICATION: true,
      RETRY_WITH_BACKUP: true,
    },
    
    // When completely offline
    OFFLINE_MODE: {
      USE_CACHED_DATA: true,
      QUEUE_OPERATIONS: true,
      LIMIT_FUNCTIONALITY: true,
      SHOW_OFFLINE_INDICATOR: true,
    },
    
    // When service is degraded
    DEGRADED_MODE: {
      REDUCE_FUNCTIONALITY: true,
      INCREASE_TIMEOUTS: true,
      LIMIT_CONCURRENT_REQUESTS: true,
      PRIORITIZE_CRITICAL_OPERATIONS: true,
    },
  },

  // Notification settings
  NOTIFICATIONS: {
    NETWORK_STATUS: {
      ONLINE: { message: 'Connection restored', severity: 'success' },
      OFFLINE: { message: 'Connection lost', severity: 'error' },
      DEGRADED: { message: 'Connection issues detected', severity: 'warning' },
    },
    
    ERROR_NOTIFICATIONS: {
      NETWORK_ERROR: { showToast: true, severity: 'error' },
      TIMEOUT_ERROR: { showToast: true, severity: 'warning' },
      RATE_LIMIT_ERROR: { showToast: true, severity: 'info' },
      SERVER_ERROR: { showToast: true, severity: 'error' },
      OFFLINE_MODE: { showToast: true, severity: 'info' },
    },
  },

  // Debug and development settings
  DEBUG: {
    ENABLE_DEBUG_LOGGING: process.env.NODE_ENV === 'development',
    ENABLE_REQUEST_LOGGING: process.env.NODE_ENV === 'development',
    ENABLE_RESPONSE_LOGGING: process.env.NODE_ENV === 'development',
    ENABLE_ERROR_STACK_TRACES: process.env.NODE_ENV === 'development',
    SIMULATE_NETWORK_FAILURES: false, // For testing only
    SIMULATE_LATENCY: 0, // Milliseconds to add for testing
  },
};

/**
 * Network utility functions
 */
export const NetworkUtils = {
  /**
   * Check if error is network-related
   */
  isNetworkError(error) {
    if (!error) return false;
    
    return (
      !error.response || // No response (network failure)
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ENOTFOUND' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('timeout') ||
      error.message?.includes('Failed to fetch')
    );
  },

  /**
   * Check if error is retryable
   */
  isRetryableError(error) {
    if (!error) return false;
    
    // Network errors are always retryable
    if (this.isNetworkError(error)) return true;
    
    // HTTP status codes that are retryable
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    if (error.response?.status && retryableStatuses.includes(error.response.status)) {
      return true;
    }
    
    return false;
  },

  /**
   * Calculate exponential backoff delay
   */
  calculateBackoffDelay(attempt, baseDelay = NETWORK_CONFIG.CONNECTION.RETRY_DELAY_BASE) {
    const maxDelay = NETWORK_CONFIG.CONNECTION.RETRY_DELAY_MAX;
    const exponentialDelay = baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 1000; // Add jitter to prevent thundering herd
    return Math.min(exponentialDelay + jitter, maxDelay);
  },

  /**
   * Get endpoint priority
   */
  getEndpointPriority(endpoint) {
    if (NETWORK_CONFIG.API_ENDPOINTS.CRITICAL.includes(endpoint)) return 'CRITICAL';
    if (NETWORK_CONFIG.API_ENDPOINTS.IMPORTANT.includes(endpoint)) return 'IMPORTANT';
    if (NETWORK_CONFIG.API_ENDPOINTS.STANDARD.includes(endpoint)) return 'STANDARD';
    if (NETWORK_CONFIG.API_ENDPOINTS.BACKGROUND.includes(endpoint)) return 'BACKGROUND';
    return 'STANDARD';
  },

  /**
   * Assess network quality based on metrics
   */
  assessNetworkQuality(metrics) {
    const { rtt, packetLoss } = metrics;
    const thresholds = NETWORK_CONFIG.NETWORK_QUALITY;
    
    if (rtt <= thresholds.EXCELLENT.rtt && packetLoss <= thresholds.EXCELLENT.packetLoss) {
      return { quality: 'EXCELLENT', score: 100 };
    }
    if (rtt <= thresholds.GOOD.rtt && packetLoss <= thresholds.GOOD.packetLoss) {
      return { quality: 'GOOD', score: 80 };
    }
    if (rtt <= thresholds.FAIR.rtt && packetLoss <= thresholds.FAIR.packetLoss) {
      return { quality: 'FAIR', score: 60 };
    }
    if (rtt <= thresholds.POOR.rtt && packetLoss <= thresholds.POOR.packetLoss) {
      return { quality: 'POOR', score: 40 };
    }
    return { quality: 'CRITICAL', score: 20 };
  },

  /**
   * Check browser compatibility
   */
  checkBrowserCompatibility() {
    const userAgent = navigator.userAgent;
    const compatibility = { ...NETWORK_CONFIG.BROWSER_COMPATIBILITY.FEATURE_DETECTION };
    
    // Add more detailed browser detection if needed
    return {
      compatible: Object.values(compatibility).every(supported => supported),
      features: compatibility,
      userAgent
    };
  },

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Parse retry-after header
   */
  parseRetryAfter(header) {
    if (!header) return null;
    
    const seconds = parseInt(header, 10);
    if (!isNaN(seconds)) {
      return seconds * 1000; // Convert to milliseconds
    }
    
    // Handle date format (e.g., "Wed, 21 Oct 2015 07:28:00 GMT")
    const date = new Date(header);
    if (!isNaN(date.getTime())) {
      return date.getTime() - Date.now();
    }
    
    return null;
  },

  /**
   * Validate network configuration
   */
  validateConfiguration() {
    const errors = [];
    
    // Validate timeout values
    if (NETWORK_CONFIG.CONNECTION.TIMEOUT <= 0) {
      errors.push('Connection timeout must be positive');
    }
    
    // Validate retry attempts
    if (NETWORK_CONFIG.CONNECTION.RETRY_ATTEMPTS < 0) {
      errors.push('Retry attempts must be non-negative');
    }
    
    // Validate circuit breaker thresholds
    if (NETWORK_CONFIG.CIRCUIT_BREAKER.FAILURE_THRESHOLD <= 0) {
      errors.push('Circuit breaker failure threshold must be positive');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
};

/**
 * Export configuration and utilities
 */
export default {
  NETWORK_CONFIG,
  NetworkUtils
};