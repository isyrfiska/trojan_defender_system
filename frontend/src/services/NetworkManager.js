/**
 * Advanced Network Manager for Trojan Defender
 * Provides zero-fault network operations with comprehensive error handling
 */

import axios from 'axios';
import { handleError, ERROR_TYPES, ERROR_SEVERITY } from '../utils/errorHandler';

class NetworkManager {
  constructor() {
    this.circuitBreakers = new Map();
    this.healthChecks = new Map();
    this.retryQueue = new Map();
    this.offlineQueue = [];
    this.isOnline = navigator.onLine;
    this.healthCheckInterval = 30000; // 30 seconds
    this.circuitBreakerThreshold = 5; // failures before opening
    this.circuitBreakerTimeout = 60000; // 60 seconds
    this.maxRetryAttempts = 3;
    this.baseRetryDelay = 1000; // 1 second
    
    this.setupNetworkMonitoring();
    this.startHealthChecks();
  }

  /**
   * Create a circuit breaker for a specific endpoint
   */
  createCircuitBreaker(endpoint) {
    const key = this.getCircuitKey(endpoint);
    
    this.circuitBreakers.set(key, {
      failures: 0,
      successes: 0,
      state: 'CLOSED', // CLOSED, OPEN, HALF_OPEN
      lastFailureTime: null,
      nextRetryTime: null,
      endpoint
    });
    
    return this.circuitBreakers.get(key);
  }

  /**
   * Get circuit breaker for an endpoint
   */
  getCircuitBreaker(endpoint) {
    const key = this.getCircuitKey(endpoint);
    let breaker = this.circuitBreakers.get(key);
    
    if (!breaker) {
      breaker = this.createCircuitBreaker(endpoint);
    }
    
    return breaker;
  }

  /**
   * Check if circuit breaker allows the request
   */
  canExecute(endpoint) {
    const breaker = this.getCircuitBreaker(endpoint);
    const now = Date.now();
    
    switch (breaker.state) {
      case 'CLOSED':
        return true;
      case 'OPEN':
        if (now >= breaker.nextRetryTime) {
          breaker.state = 'HALF_OPEN';
          return true;
        }
        return false;
      case 'HALF_OPEN':
        return true;
      default:
        return true;
    }
  }

  /**
   * Record success for circuit breaker
   */
  recordSuccess(endpoint) {
    const breaker = this.getCircuitBreaker(endpoint);
    breaker.successes++;
    breaker.failures = 0;
    breaker.state = 'CLOSED';
    breaker.lastFailureTime = null;
  }

  /**
   * Record failure for circuit breaker
   */
  recordFailure(endpoint, error) {
    const breaker = this.getCircuitBreaker(endpoint);
    breaker.failures++;
    breaker.lastFailureTime = Date.now();
    
    if (breaker.failures >= this.circuitBreakerThreshold) {
      breaker.state = 'OPEN';
      breaker.nextRetryTime = Date.now() + this.circuitBreakerTimeout;
      
      // Log circuit breaker opening
      handleError(error, {
        context: 'circuit_breaker_opened',
        endpoint,
        failures: breaker.failures
      }, {
        showToast: true,
        severity: ERROR_SEVERITY.HIGH
      });
    }
  }

  /**
   * Setup network connectivity monitoring
   */
  setupNetworkMonitoring() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleNetworkRecovery();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleNetworkDisconnection();
    });
  }

  /**
   * Handle network disconnection
   */
  handleNetworkDisconnection() {
    handleError(
      new Error('Network connection lost'),
      { context: 'network_disconnection' },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.HIGH,
        userMessage: 'Connection lost. Working in offline mode.'
      }
    );
  }

  /**
   * Handle network recovery
   */
  handleNetworkRecovery() {
    // Process offline queue
    this.processOfflineQueue();
    
    // Reset circuit breakers
    this.circuitBreakers.forEach(breaker => {
      if (breaker.state === 'OPEN') {
        breaker.state = 'HALF_OPEN';
        breaker.nextRetryTime = Date.now();
      }
    });

    handleError(
      new Error('Network connection restored'),
      { context: 'network_recovery' },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.LOW,
        userMessage: 'Connection restored. Syncing data...'
      }
    );
  }

  /**
   * Start periodic health checks
   */
  startHealthChecks() {
    setInterval(() => {
      this.performHealthChecks();
    }, this.healthCheckInterval);
  }

  /**
   * Perform health checks on critical endpoints
   */
  async performHealthChecks() {
    const healthEndpoints = [
      '/auth/token/status/',
      '/scanner/stats/',
      '/threatmap/stats/latest/'
    ];

    for (const endpoint of healthEndpoints) {
      try {
        const startTime = Date.now();
        await this.makeRequest('GET', endpoint, null, { 
          timeout: 5000,
          healthCheck: true 
        });
        const responseTime = Date.now() - startTime;
        
        this.healthChecks.set(endpoint, {
          status: 'healthy',
          responseTime,
          lastCheck: Date.now(),
          consecutiveFailures: 0
        });
      } catch (error) {
        const currentHealth = this.healthChecks.get(endpoint) || { consecutiveFailures: 0 };
        const consecutiveFailures = currentHealth.consecutiveFailures + 1;
        
        this.healthChecks.set(endpoint, {
          status: 'unhealthy',
          lastCheck: Date.now(),
          consecutiveFailures,
          error: error.message
        });

        if (consecutiveFailures >= 3) {
          handleError(error, {
            context: 'health_check_failed',
            endpoint,
            consecutiveFailures
          }, {
            showToast: true,
            severity: ERROR_SEVERITY.HIGH
          });
        }
      }
    }
  }

  /**
   * Advanced retry mechanism with exponential backoff
   */
  async retryWithBackoff(fn, attempts = 0, endpoint = null) {
    if (attempts >= this.maxRetryAttempts) {
      throw new Error(`Max retry attempts (${this.maxRetryAttempts}) exceeded`);
    }

    try {
      return await fn();
    } catch (error) {
      if (this.isRetryableError(error) && attempts < this.maxRetryAttempts) {
        const delay = this.baseRetryDelay * Math.pow(2, attempts) + Math.random() * 1000;
        
        handleError(error, {
          context: 'retry_attempt',
          attempt: attempts + 1,
          maxAttempts: this.maxRetryAttempts,
          nextRetryDelay: delay,
          endpoint
        }, {
          showToast: false,
          severity: ERROR_SEVERITY.MEDIUM
        });

        await this.delay(delay);
        return this.retryWithBackoff(fn, attempts + 1, endpoint);
      }
      throw error;
    }
  }

  /**
   * Check if error is retryable
   */
  isRetryableError(error) {
    if (!error.response) {
      // Network errors are retryable
      return true;
    }

    const status = error.response.status;
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    return retryableStatuses.includes(status);
  }

  /**
   * Queue request for offline processing
   */
  queueForOffline(request) {
    this.offlineQueue.push({
      ...request,
      timestamp: Date.now(),
      id: this.generateRequestId()
    });
  }

  /**
   * Process offline queue when network is restored
   */
  async processOfflineQueue() {
    const queue = [...this.offlineQueue];
    this.offlineQueue = [];

    for (const request of queue) {
      try {
        await this.makeRequest(request.method, request.endpoint, request.data, request.options);
      } catch (error) {
        // Re-queue failed requests
        this.queueForOffline(request);
      }
    }
  }

  /**
   * Main request method with all protections
   */
  async makeRequest(method, endpoint, data = null, options = {}) {
    // Check if we're online
    if (!this.isOnline && !options.healthCheck) {
      this.queueForOffline({ method, endpoint, data, options });
      throw new Error('Network offline - request queued');
    }

    // Check circuit breaker
    if (!this.canExecute(endpoint)) {
      throw new Error(`Circuit breaker open for endpoint: ${endpoint}`);
    }

    const config = {
      method,
      url: endpoint,
      data,
      timeout: options.timeout || 30000,
      ...options
    };

    try {
      const response = await this.retryWithBackoff(
        () => axios(config),
        0,
        endpoint
      );

      this.recordSuccess(endpoint);
      return response;
    } catch (error) {
      this.recordFailure(endpoint, error);
      throw error;
    }
  }

  /**
   * Helper methods
   */
  getCircuitKey(endpoint) {
    return endpoint.split('/')[1] || 'default';
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  generateRequestId() {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get network health status
   */
  getNetworkHealth() {
    const healthChecks = Array.from(this.healthChecks.entries());
    const circuitBreakers = Array.from(this.circuitBreakers.entries());
    
    return {
      isOnline: this.isOnline,
      healthChecks,
      circuitBreakers,
      offlineQueueSize: this.offlineQueue.length,
      timestamp: Date.now()
    };
  }
}

// Create singleton instance
const networkManager = new NetworkManager();
export default networkManager;