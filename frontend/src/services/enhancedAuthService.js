import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { handleError, ERROR_TYPES } from '../utils/errorHandler';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class EnhancedAuthService {
  constructor() {
    this.api = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000, // 10 second timeout
    });

    // Token refresh state management
    this.isRefreshing = false;
    this.refreshPromise = null;
    this.failedQueue = [];
    this.refreshAttempts = 0;
    this.maxRetries = 3;
    this.proactiveRefreshTimer = null;
    
    // Proactive refresh threshold (5 minutes before expiry)
    this.REFRESH_THRESHOLD_MS = 5 * 60 * 1000;
    
    this.setupInterceptors();
    this.startProactiveRefresh();
  }

  setupInterceptors() {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add request metadata for error handling
        config.metadata = {
          startTime: Date.now(),
          endpoint: config.url,
          method: config.method?.toUpperCase()
        };
        
        return config;
      },
      (error) => {
        handleError(error, { context: 'request_interceptor' });
        return Promise.reject(error);
      }
    );

    // Response interceptor with enhanced error handling
    this.api.interceptors.response.use(
      (response) => {
        // Add response timing
        if (response.config.metadata) {
          response.config.metadata.duration = Date.now() - response.config.metadata.startTime;
        }
        
        // Reset refresh attempts on successful request
        this.refreshAttempts = 0;
        
        return response;
      },
      async (error) => {
        const originalRequest = error.config;
        
        // Enhanced error context
        const errorContext = {
          endpoint: originalRequest?.url,
          method: originalRequest?.method?.toUpperCase(),
          duration: originalRequest?.metadata?.startTime ? 
            Date.now() - originalRequest.metadata.startTime : null,
          status: error.response?.status,
          retryAttempt: originalRequest._retryCount || 0
        };

        // Handle 401 errors with token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue the request while refresh is in progress
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject, config: originalRequest });
            });
          }

          originalRequest._retry = true;
          
          try {
            await this.handleTokenRefresh();
            return this.api(originalRequest);
          } catch (refreshError) {
            this.processFailedQueue(refreshError);
            handleError(refreshError, { 
              ...errorContext, 
              context: 'token_refresh_failed' 
            });
            this.logout();
            return Promise.reject(refreshError);
          }
        }

        // Handle network errors with retry logic
        if (this.isNetworkError(error) && this.shouldRetry(originalRequest)) {
          return this.retryRequest(originalRequest, errorContext);
        }

        // Handle all other errors
        handleError(error, errorContext, {
          showToast: !originalRequest._suppressErrorToast,
          enableRetry: this.shouldRetry(originalRequest),
          onRetry: (attempt) => this.retryRequest(originalRequest, errorContext, attempt)
        });

        return Promise.reject(error);
      }
    );
  }

  async handleTokenRefresh() {
    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshAttempts++;

    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      this.refreshPromise = this.api.post('/auth/token/refresh/', {
        refresh: refreshToken
      });

      const response = await this.refreshPromise;
      const { access, refresh } = response.data;

      localStorage.setItem('token', access);
      if (refresh) {
        localStorage.setItem('refreshToken', refresh);
      }

      this.processFailedQueue(null, access);
      this.refreshAttempts = 0;
      
      return response;
    } catch (error) {
      this.processFailedQueue(error);
      throw error;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  processFailedQueue(error, token = null) {
    this.failedQueue.forEach(({ resolve, reject, config }) => {
      if (error) {
        reject(error);
      } else {
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        resolve(this.api(config));
      }
    });
    
    this.failedQueue = [];
  }

  isNetworkError(error) {
    return !error.response && (
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('timeout')
    );
  }

  shouldRetry(config) {
    const retryCount = config._retryCount || 0;
    const maxRetries = config._maxRetries || 3;
    const retryMethods = ['GET', 'HEAD', 'OPTIONS', 'PUT'];
    
    return retryCount < maxRetries && 
           retryMethods.includes(config.method?.toUpperCase()) &&
           !config._noRetry;
  }

  async retryRequest(config, errorContext, attempt = null) {
    const retryCount = config._retryCount || 0;
    const delay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Exponential backoff, max 10s
    
    config._retryCount = retryCount + 1;
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    try {
      return await this.api(config);
    } catch (retryError) {
      if (this.shouldRetry(config)) {
        return this.retryRequest(config, errorContext);
      }
      throw retryError;
    }
  }

  // Enhanced login method
  async login(email, password) {
    try {
      console.log('EnhancedAuthService: Making login request to /auth/login/'); // Debug log
      const response = await this.api.post('/auth/login/', {
        email: email,
        password: password
      });
      
      console.log('EnhancedAuthService: Login response received:', response.status); // Debug log
      
      const { access, refresh, user } = response.data;
      
      if (!access || !refresh) {
        console.error('EnhancedAuthService: Missing tokens in response'); // Debug log
        throw new Error('Invalid response: missing authentication tokens');
      }
      
      localStorage.setItem('token', access);
      localStorage.setItem('refreshToken', refresh);
      
      // Start proactive refresh
      this.startProactiveRefresh();
      
      console.log('EnhancedAuthService: Login successful, tokens stored'); // Debug log
      return response;
    } catch (error) {
      console.error('EnhancedAuthService: Login error:', error); // Debug log
      handleError(error, { 
        context: 'login',
        email: email // Don't log password
      }, {
        showToast: false // Disable toast here, let the component handle it
      });
      throw error;
    }
  }

  // Enhanced register method
  async register(userData) {
    try {
      const response = await this.api.post('/auth/register/', userData);
      return response;
    } catch (error) {
      handleError(error, { 
        context: 'registration',
        userData: { ...userData, password: '[REDACTED]' }
      });
      throw error;
    }
  }

  // Enhanced getCurrentUser method
  async getCurrentUser() {
    try {
      const response = await this.api.get('/auth/profile/');
      return response;
    } catch (error) {
      handleError(error, { context: 'get_current_user' });
      throw error;
    }
  }

  // Enhanced refresh token method
  async refreshToken(refreshToken) {
    try {
      const response = await this.api.post('/auth/token/refresh/', {
        refresh: refreshToken
      });
      return response;
    } catch (error) {
      handleError(error, { context: 'refresh_token' });
      throw error;
    }
  }

  // Enhanced logout method
  logout() {
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      
      // Clear proactive refresh timer
      if (this.proactiveRefreshTimer) {
        clearInterval(this.proactiveRefreshTimer);
        this.proactiveRefreshTimer = null;
      }
      
      // Clear any pending refresh state
      this.isRefreshing = false;
      this.refreshPromise = null;
      this.failedQueue = [];
      this.refreshAttempts = 0;
      
    } catch (error) {
      handleError(error, { context: 'logout' }, { showToast: false });
    }
  }

  // Enhanced token status check
  getTokenStatus() {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        return { valid: false, expired: true };
      }

      const decoded = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      const expired = decoded.exp < currentTime;
      const expiresIn = (decoded.exp - currentTime) * 1000;

      return {
        valid: !expired,
        expired,
        expiresIn,
        expiresAt: new Date(decoded.exp * 1000),
        userId: decoded.user_id,
        username: decoded.username
      };
    } catch (error) {
      handleError(error, { context: 'token_status_check' }, { showToast: false });
      return { valid: false, expired: true };
    }
  }

  // Proactive token refresh
  startProactiveRefresh() {
    if (this.proactiveRefreshTimer) {
      clearInterval(this.proactiveRefreshTimer);
    }

    this.proactiveRefreshTimer = setInterval(() => {
      const tokenStatus = this.getTokenStatus();
      
      if (tokenStatus.valid && tokenStatus.expiresIn < this.REFRESH_THRESHOLD_MS) {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken && !this.isRefreshing) {
          this.handleTokenRefresh().catch(error => {
            handleError(error, { context: 'proactive_refresh' }, { showToast: false });
          });
        }
      }
    }, 60000); // Check every minute
  }

  // Health check method
  async healthCheck() {
    try {
      const response = await this.api.get('/health/', {
        _suppressErrorToast: true,
        _noRetry: true
      });
      return response;
    } catch (error) {
      handleError(error, { context: 'health_check' }, { showToast: false });
      throw error;
    }
  }

  // Get service statistics
  getServiceStats() {
    return {
      refreshAttempts: this.refreshAttempts,
      isRefreshing: this.isRefreshing,
      queuedRequests: this.failedQueue.length,
      proactiveRefreshActive: !!this.proactiveRefreshTimer
    };
  }
}

export default new EnhancedAuthService();