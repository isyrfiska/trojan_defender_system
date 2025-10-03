/**
 * Comprehensive Network Error Handling Tests
 * Tests all components of the zero-fault network error handling system
 */

import networkManager from '../NetworkManager';
import enhancedAxios from '../EnhancedAxios';
import offlineModeHandler from '../OfflineModeHandler';
import { handleError, ERROR_TYPES } from '../../utils/errorHandler';

// Mock dependencies
jest.mock('axios');
jest.mock('../NetworkManager');
jest.mock('../../utils/errorHandler');

describe('Network Error Handling System', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Reset network manager state
    if (networkManager.circuitBreakers) {
      networkManager.circuitBreakers.clear();
    }
    if (networkManager.offlineQueue) {
      networkManager.offlineQueue = [];
    }
    
    // Reset offline mode handler
    if (offlineModeHandler.offlineQueue) {
      offlineModeHandler.offlineQueue = [];
    }
    if (offlineModeHandler.offlineCache) {
      offlineModeHandler.offlineCache.clear();
    }
  });

  describe('NetworkManager', () => {
    test('should create circuit breaker for new endpoints', () => {
      const endpoint = '/api/test/endpoint';
      const breaker = networkManager.createCircuitBreaker(endpoint);
      
      expect(breaker).toBeDefined();
      expect(breaker.state).toBe('CLOSED');
      expect(breaker.failures).toBe(0);
      expect(breaker.endpoint).toBe(endpoint);
    });

    test('should record failures and open circuit breaker', () => {
      const endpoint = '/api/test/endpoint';
      const breaker = networkManager.createCircuitBreaker(endpoint);
      const error = new Error('Network error');
      
      // Record failures up to threshold
      for (let i = 0; i < 5; i++) {
        networkManager.recordFailure(endpoint, error);
      }
      
      expect(breaker.state).toBe('OPEN');
      expect(breaker.failures).toBe(5);
      expect(breaker.nextRetryTime).toBeGreaterThan(Date.now());
    });

    test('should prevent requests when circuit breaker is open', () => {
      const endpoint = '/api/test/endpoint';
      const breaker = networkManager.createCircuitBreaker(endpoint);
      
      // Open the circuit breaker
      breaker.state = 'OPEN';
      breaker.nextRetryTime = Date.now() + 60000;
      
      const canExecute = networkManager.canExecute(endpoint);
      expect(canExecute).toBe(false);
    });

    test('should handle network disconnection and recovery', () => {
      // Test offline handling
      networkManager.handleNetworkDisconnection();
      expect(networkManager.isOnline).toBe(false);
      
      // Test online handling
      networkManager.handleNetworkRecovery();
      expect(networkManager.isOnline).toBe(true);
    });

    test('should queue requests when offline', () => {
      networkManager.isOnline = false;
      
      const request = {
        method: 'GET',
        endpoint: '/api/test',
        data: null
      };
      
      networkManager.queueForOffline(request);
      expect(networkManager.offlineQueue.length).toBe(1);
      expect(networkManager.offlineQueue[0]).toEqual(expect.objectContaining(request));
    });

    test('should retry with exponential backoff', async () => {
      const mockFn = jest.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: 'success' });
      
      const result = await networkManager.retryWithBackoff(mockFn, 0, '/api/test');
      
      expect(mockFn).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ data: 'success' });
    });

    test('should identify retryable errors correctly', () => {
      const retryableErrors = [
        { code: 'NETWORK_ERROR' },
        { code: 'ECONNABORTED' },
        { message: 'Network Error' },
        { message: 'timeout exceeded' },
        { response: { status: 408 } },
        { response: { status: 429 } },
        { response: { status: 503 } }
      ];
      
      retryableErrors.forEach(error => {
        expect(networkManager.isRetryableError(error)).toBe(true);
      });
      
      const nonRetryableErrors = [
        { response: { status: 400 } },
        { response: { status: 401 } },
        { response: { status: 403 } }
      ];
      
      nonRetryableErrors.forEach(error => {
        expect(networkManager.isRetryableError(error)).toBe(false);
      });
    });
  });

  describe('EnhancedAxios', () => {
    test('should create axios instance with enhanced configuration', () => {
      const instance = enhancedAxios.createInstance('test', {
        timeout: 5000,
        headers: { 'X-Custom-Header': 'test' }
      });
      
      expect(instance).toBeDefined();
      expect(enhancedAxios.instances.has('test')).toBe(true);
    });

    test('should handle HTTP errors correctly', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        },
        config: {
          url: '/api/test',
          method: 'GET',
          metadata: {
            retryCount: 0,
            maxRetries: 3
          }
        }
      };
      
      const result = await enhancedAxios.handleHttpError(mockError, {}, mockError.config.metadata);
      expect(result).toBeDefined();
    });

    test('should handle timeout errors with retry', async () => {
      const mockError = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
        config: {
          url: '/api/test',
          method: 'GET',
          metadata: {
            retryCount: 0,
            maxRetries: 3
          }
        }
      };
      
      // Mock retry logic
      const retrySpy = jest.spyOn(enhancedAxios, 'retryRequest').mockResolvedValue({ data: 'success' });
      
      const result = await enhancedAxios.handleTimeoutError(mockError, {}, mockError.config.metadata);
      expect(retrySpy).toHaveBeenCalled();
    });

    test('should handle unauthorized errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' }
        },
        config: {
          url: '/api/test',
          method: 'GET'
        }
      };
      
      const result = await enhancedAxios.handleUnauthorizedError(mockError, {}, {});
      expect(result).toBeDefined();
    });

    test('should handle rate limit errors', async () => {
      const mockError = {
        response: {
          status: 429,
          headers: { 'retry-after': '60' },
          data: { message: 'Too many requests' }
        },
        config: {
          url: '/api/test',
          method: 'GET'
        }
      };
      
      const result = await enhancedAxios.handleRateLimitError(mockError, {}, {});
      expect(result).toBeDefined();
    });
  });

  describe('OfflineModeHandler', () => {
    test('should handle offline mode transitions', () => {
      const callback = jest.fn();
      offlineModeHandler.addCallback(callback);
      
      // Test offline transition
      offlineModeHandler.handleOffline();
      expect(offlineModeHandler.isOffline).toBe(true);
      expect(callback).toHaveBeenCalledWith('offline', true);
      
      // Test online transition
      offlineModeHandler.handleOnline();
      expect(offlineModeHandler.isOffline).toBe(false);
      expect(callback).toHaveBeenCalledWith('online', false);
    });

    test('should queue actions when offline', () => {
      offlineModeHandler.isOffline = true;
      
      const action = {
        type: 'SCAN_UPLOAD',
        data: { file: 'test.txt' }
      };
      
      const actionId = offlineModeHandler.queueAction(action);
      expect(actionId).toBeDefined();
      expect(offlineModeHandler.offlineQueue.length).toBe(1);
      expect(offlineModeHandler.offlineQueue[0]).toEqual(expect.objectContaining({
        type: 'SCAN_UPLOAD',
        data: { file: 'test.txt' },
        status: 'pending'
      }));
    });

    test('should cache data for offline access', () => {
      const testData = { key: 'value' };
      const key = 'test_key';
      
      offlineModeHandler.cacheData(key, testData);
      
      const cachedData = offlineModeHandler.getCachedData(key);
      expect(cachedData).toEqual(testData);
    });

    test('should handle cache expiry', (done) => {
      const testData = { key: 'value' };
      const key = 'test_key';
      
      // Cache with 100ms expiry
      offlineModeHandler.cacheData(key, testData, 100);
      
      // Should return data immediately
      expect(offlineModeHandler.getCachedData(key)).toEqual(testData);
      
      // Should return null after expiry
      setTimeout(() => {
        expect(offlineModeHandler.getCachedData(key)).toBeNull();
        done();
      }, 150);
    });

    test('should limit queue size', () => {
      offlineModeHandler.isOffline = true;
      offlineModeHandler.maxQueueSize = 5;
      
      // Queue more actions than max size
      for (let i = 0; i < 10; i++) {
        offlineModeHandler.queueAction({
          type: 'TEST_ACTION',
          data: { index: i }
        });
      }
      
      expect(offlineModeHandler.offlineQueue.length).toBe(5);
      expect(offlineModeHandler.offlineQueue[0].data.index).toBe(5); // Oldest actions removed
    });

    test('should provide queue status', () => {
      offlineModeHandler.isOffline = true;
      
      // Add some test actions
      offlineModeHandler.queueAction({ type: 'TEST_1', data: {} });
      offlineModeHandler.queueAction({ type: 'TEST_2', data: {} });
      
      const status = offlineModeHandler.getQueueStatus();
      expect(status.total).toBe(2);
      expect(status.pending).toBe(2);
      expect(status.processing).toBe(0);
      expect(status.failed).toBe(0);
      expect(status.completed).toBe(0);
    });
  });

  describe('Integration Tests', () => {
    test('should handle complete network failure scenario', async () => {
      // Simulate network failure
      const networkError = new Error('Network Error');
      networkError.code = 'NETWORK_ERROR';
      
      // Record failure in circuit breaker
      const endpoint = '/api/critical/endpoint';
      networkManager.recordFailure(endpoint, networkError);
      
      // Check circuit breaker state
      const breaker = networkManager.getCircuitBreaker(endpoint);
      expect(breaker.failures).toBe(1);
      
      // Simulate offline mode
      offlineModeHandler.handleOffline();
      expect(offlineModeHandler.isOffline).toBe(true);
      
      // Queue action while offline
      const actionId = offlineModeHandler.queueAction({
        type: 'CRITICAL_ACTION',
        data: { important: 'data' }
      });
      
      expect(actionId).toBeDefined();
      expect(offlineModeHandler.offlineQueue.length).toBe(1);
      
      // Simulate network recovery
      offlineModeHandler.handleOnline();
      expect(offlineModeHandler.isOffline).toBe(false);
      
      // Circuit breaker should be in half-open state
      expect(breaker.state).toBe('HALF_OPEN');
    });

    test('should handle rate limiting with backoff', async () => {
      const rateLimitError = {
        response: {
          status: 429,
          headers: { 'retry-after': '10' }
        }
      };
      
      const endpoint = '/api/rate-limited/endpoint';
      
      // Simulate multiple rate limit errors
      for (let i = 0; i < 3; i++) {
        networkManager.recordFailure(endpoint, rateLimitError);
      }
      
      // Should implement backoff strategy
      const breaker = networkManager.getCircuitBreaker(endpoint);
      expect(breaker.failures).toBe(3);
    });
  });

  describe('Performance Tests', () => {
    test('should handle high volume of network errors efficiently', async () => {
      const startTime = Date.now();
      const errorCount = 1000;
      
      // Simulate many network errors
      for (let i = 0; i < errorCount; i++) {
        const error = new Error(`Network error ${i}`);
        error.code = 'NETWORK_ERROR';
        networkManager.recordFailure('/api/stress/test', error);
      }
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // Should handle 1000 errors in reasonable time (< 1 second)
      expect(duration).toBeLessThan(1000);
      
      // Circuit breaker should be open
      const breaker = networkManager.getCircuitBreaker('/api/stress/test');
      expect(breaker.state).toBe('OPEN');
    });

    test('should handle concurrent retry attempts', async () => {
      const retryPromises = [];
      
      // Create multiple concurrent retry attempts
      for (let i = 0; i < 10; i++) {
        const promise = networkManager.retryWithBackoff(
          () => Promise.resolve({ success: true, id: i }),
          0,
          '/api/concurrent/test'
        );
        retryPromises.push(promise);
      }
      
      const results = await Promise.all(retryPromises);
      
      expect(results).toHaveLength(10);
      results.forEach((result, index) => {
        expect(result).toEqual({ success: true, id: index });
      });
    });
  });
});