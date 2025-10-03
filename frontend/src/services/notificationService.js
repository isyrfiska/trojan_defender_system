import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance for notification API calls
const notificationAPI = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor to add auth token
notificationAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
notificationAPI.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const notificationService = {
  /**
   * Get user notification preferences
   */
  async getNotificationPreferences() {
    try {
      const response = await notificationAPI.get('/users/profile/');
      return {
        notify_scan_complete: response.data.notify_scan_complete,
        notify_security_alerts: response.data.notify_security_alerts,
      };
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
      throw error;
    }
  },

  /**
   * Update user notification preferences
   * @param {Object} preferences - Notification preferences
   * @param {boolean} preferences.notify_scan_complete - Enable scan completion notifications
   * @param {boolean} preferences.notify_security_alerts - Enable security alert notifications
   */
  async updateNotificationPreferences(preferences) {
    try {
      const response = await notificationAPI.patch('/users/profile/', preferences);
      return response.data;
    } catch (error) {
      console.error('Error updating notification preferences:', error);
      throw error;
    }
  },

  /**
   * Test email notification system
   */
  async testEmailNotification() {
    try {
      const response = await notificationAPI.post('/users/test-email/');
      return response.data;
    } catch (error) {
      console.error('Error testing email notification:', error);
      throw error;
    }
  },

  /**
   * Get notification history
   * @param {number} page - Page number
   * @param {number} pageSize - Number of items per page
   */
  async getNotificationHistory(page = 1, pageSize = 20) {
    try {
      const response = await notificationAPI.get('/notifications/', {
        params: {
          page,
          page_size: pageSize,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching notification history:', error);
      throw error;
    }
  },

  /**
   * Mark notification as read
   * @param {string} notificationId - Notification ID
   */
  async markNotificationAsRead(notificationId) {
    try {
      const response = await notificationAPI.patch(`/notifications/${notificationId}/`, {
        is_read: true,
      });
      return response.data;
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  },

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsAsRead() {
    try {
      const response = await notificationAPI.post('/notifications/mark-all-read/');
      return response.data;
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      throw error;
    }
  },

  /**
   * Delete notification
   * @param {string} notificationId - Notification ID
   */
  async deleteNotification(notificationId) {
    try {
      await notificationAPI.delete(`/notifications/${notificationId}/`);
      return true;
    } catch (error) {
      console.error('Error deleting notification:', error);
      throw error;
    }
  },

  /**
   * Get unread notification count
   */
  async getUnreadCount() {
    try {
      const response = await notificationAPI.get('/notifications/unread-count/');
      return response.data.count;
    } catch (error) {
      console.error('Error fetching unread count:', error);
      throw error;
    }
  },
};

export default notificationService;