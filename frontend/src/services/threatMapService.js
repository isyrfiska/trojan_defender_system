import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token refresh and rate limiting
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle rate limiting
    if (error.response?.status === 429) {
      const waitTime = error.response.data?.wait || 60;
      console.warn(`Rate limit exceeded. Retrying after ${waitTime} seconds...`);
      
      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
      return apiClient(originalRequest);
    }
    
    // Handle authentication errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          const newToken = response.data.access;
          localStorage.setItem('token', newToken);
          
          // Retry original request with new token
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Clear tokens but don't redirect
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
      }
    }
    
    return Promise.reject(error);
  }
);

class ThreatMapService {
  constructor() {
    this.baseURL = '/threatmap';
  }

  /**
   * Get threat map data with filtering and caching
   * @param {Object} params - Query parameters
   * @param {number} params.days - Number of days to look back
   * @param {string} params.threat_type - Filter by threat type
   * @param {string} params.severity - Filter by severity level
   * @param {string} params.country - Filter by country
   * @returns {Promise<Object>} Threat map data with heat map points and statistics
   */
  async getMapData(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/threats/`, {
        params: {
          days: params.days || 30,
          threat_type: params.threat_type || '',
          severity: params.severity || '',
          country: params.country || '',
        }
      });

      return {
        success: true,
        data: response.data,
        threats: response.data.threats || [],
        heatData: response.data.heat_data || [],
        statistics: response.data.statistics || {},
        totalCount: response.data.total_count || 0,
        dateRange: response.data.date_range || {},
        filters: response.data.filters || {},
      };
    } catch (error) {
      console.error('Error fetching threat map data:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
        threats: [],
        heatData: [],
        statistics: {},
        totalCount: 0,
      };
    }
  }

  /**
   * Get real-time threat data with advanced filtering
   * @param {Object} params - Query parameters
   * @param {number} params.days - Number of days to look back
   * @param {string} params.threat_type - Filter by threat type
   * @param {string} params.severity - Filter by severity level
   * @param {string} params.country - Filter by country
   * @param {string} params.last_update - ISO timestamp for incremental updates
   * @returns {Promise<Object>} Real-time threat data
   */
  async getRealTimeData(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/threats/realtime/`, {
        params: {
          days: params.days || 1,
          threat_type: params.threat_type || '',
          severity: params.severity || '',
          country: params.country || '',
          last_update: params.last_update || '',
        }
      });

      return {
        success: true,
        data: response.data,
        threats: response.data.threats || [],
        totalCount: response.data.total_count || 0,
        lastUpdate: response.data.last_update,
        filtersApplied: response.data.filters_applied || {},
      };
    } catch (error) {
      console.error('Error fetching real-time threat data:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
        threats: [],
        totalCount: 0,
        lastUpdate: null,
      };
    }
  }

  /**
   * Get all threat events with pagination
   * @param {Object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.page_size - Items per page
   * @param {string} params.ordering - Sort order
   * @returns {Promise<Object>} Paginated threat events
   */
  async getThreatEvents(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/threats/`, {
        params: {
          page: params.page || 1,
          page_size: params.page_size || 50,
          ordering: params.ordering || '-timestamp',
          ...params
        }
      });

      return {
        success: true,
        data: response.data,
        results: response.data.results || [],
        count: response.data.count || 0,
        next: response.data.next,
        previous: response.data.previous,
      };
    } catch (error) {
      console.error('Error fetching threat events:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
        results: [],
        count: 0,
      };
    }
  }

  /**
   * Get a specific threat event by ID
   * @param {string} threatId - Threat event ID
   * @returns {Promise<Object>} Threat event details
   */
  async getThreatEvent(threatId) {
    try {
      const response = await apiClient.get(`${this.baseURL}/events/${threatId}/`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Error fetching threat event:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
      };
    }
  }

  /**
   * Create a new threat event
   * @param {Object} threatData - Threat event data
   * @returns {Promise<Object>} Created threat event
   */
  async createThreatEvent(threatData) {
    try {
      const response = await apiClient.post(`${this.baseURL}/events/`, threatData);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Error creating threat event:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
      };
    }
  }

  /**
   * Generate threat map report
   * @param {Object} params - Report parameters
   * @param {string} params.format - Report format (pdf, json, csv)
   * @param {number} params.days - Number of days to include
   * @param {string} params.threat_type - Filter by threat type
   * @param {string} params.severity - Filter by severity
   * @returns {Promise<Object>} Report generation result
   */
  async generateReport(params = {}) {
    try {
      const response = await apiClient.post(`${this.baseURL}/events/report/`, {
        format: params.format || 'pdf',
        days: params.days || 30,
        threat_type: params.threat_type || '',
        severity: params.severity || '',
        include_charts: params.include_charts !== false,
        include_statistics: params.include_statistics !== false,
      });

      return {
        success: true,
        data: response.data,
        reportUrl: response.data.report_url,
        reportId: response.data.report_id,
      };
    } catch (error) {
      console.error('Error generating report:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
      };
    }
  }

  /**
   * Get threat trends over time
   * @param {Object} params - Query parameters
   * @param {number} params.days - Number of days to analyze
   * @param {string} params.interval - Time interval (hour, day, week)
   * @param {string} params.threat_type - Filter by threat type
   * @param {string} params.severity - Filter by severity
   * @returns {Promise<Object>} Threat trend data
   */
  async getThreatTrends(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/trends/`, {
        params: {
          days: params.days || 30,
          interval: params.interval || 'day',
          threat_type: params.threat_type || '',
          severity: params.severity || '',
        }
      });

      return {
        success: true,
        data: response.data,
        trends: response.data.trends || [],
        summary: response.data.summary || {},
      };
    } catch (error) {
      console.error('Error fetching threat trends:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: null,
        trends: [],
        summary: {},
      };
    }
  }
}

// Create and export a singleton instance
const threatMapService = new ThreatMapService();
export default threatMapService;