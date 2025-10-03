import enhancedAxios from './EnhancedAxios';

// Get enhanced axios instance
const api = enhancedAxios.getInstance('dashboard');

// Add request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const dashboardService = {
  // Get dashboard statistics
  getDashboardStats: async () => {
    try {
      // Get scan statistics
      const scanStatsResponse = await api.get('/scanner/stats/');
      
      // Get threat statistics
      const threatStatsResponse = await api.get('/threatmap/stats/latest/');
      
      // Get recent scans (last 5)
      const recentScansResponse = await api.get('/scanner/results/', {
        params: { 
          ordering: '-upload_date',
          limit: 5 
        }
      });

      return {
        scanStats: scanStatsResponse.data,
        threatStats: threatStatsResponse.data,
        recentScans: recentScansResponse.data.results || recentScansResponse.data
      };
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  },

  // Get recent scan results
  getRecentScans: async (limit = 10) => {
    try {
      const response = await api.get('/scanner/results/', {
        params: { 
          ordering: '-upload_date',
          limit 
        }
      });
      return response.data.results || response.data;
    } catch (error) {
      console.error('Error fetching recent scans:', error);
      throw error;
    }
  },

  // Get scan statistics
  getScanStatistics: async () => {
    try {
      const response = await api.get('/scanner/stats/');
      return response.data;
    } catch (error) {
      console.error('Error fetching scan statistics:', error);
      throw error;
    }
  },

  // Get threat statistics
  getThreatStatistics: async () => {
    try {
      const response = await api.get('/threatmap/stats/latest/');
      return response.data;
    } catch (error) {
      console.error('Error fetching threat statistics:', error);
      throw error;
    }
  },

  // Get user profile for dashboard personalization
  getUserProfile: async () => {
    try {
      const response = await api.get('/users/profile/');
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  }
};

export default dashboardService;