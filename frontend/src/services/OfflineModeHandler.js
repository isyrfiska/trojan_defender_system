/**
 * Offline Mode Handler
 * Provides graceful degradation and offline functionality
 */

import { handleError, ERROR_TYPES, ERROR_SEVERITY } from '../utils/errorHandler';

class OfflineModeHandler {
  constructor() {
    this.isOffline = !navigator.onLine;
    this.offlineQueue = [];
    this.offlineCache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
    this.maxQueueSize = 100;
    this.offlineModeCallbacks = new Set();
    
    this.setupOfflineDetection();
    this.loadOfflineCache();
  }

  /**
   * Setup offline detection
   */
  setupOfflineDetection() {
    window.addEventListener('online', () => {
      this.handleOnline();
    });

    window.addEventListener('offline', () => {
      this.handleOffline();
    });
  }

  /**
   * Handle going online
   */
  async handleOnline() {
    this.isOffline = false;
    
    handleError(
      new Error('Network connection restored'),
      { context: 'offline_to_online' },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.LOW,
        userMessage: 'Connection restored. Processing offline actions...'
      }
    );

    // Process offline queue
    await this.processOfflineQueue();
    
    // Notify callbacks
    this.notifyCallbacks('online');
  }

  /**
   * Handle going offline
   */
  handleOffline() {
    this.isOffline = true;
    
    handleError(
      new Error('Network connection lost'),
      { context: 'online_to_offline' },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.MEDIUM,
        userMessage: 'Connection lost. Working in offline mode.'
      }
    );

    // Notify callbacks
    this.notifyCallbacks('offline');
  }

  /**
   * Queue action for offline processing
   */
  queueAction(action) {
    if (this.offlineQueue.length >= this.maxQueueSize) {
      // Remove oldest action
      this.offlineQueue.shift();
    }

    const queuedAction = {
      id: this.generateActionId(),
      type: action.type,
      data: action.data,
      timestamp: Date.now(),
      status: 'pending',
      retries: 0,
      maxRetries: 3
    };

    this.offlineQueue.push(queuedAction);
    this.saveOfflineQueue();

    handleError(
      new Error(`Action queued for offline processing: ${action.type}`),
      { context: 'action_queued', actionId: queuedAction.id },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.LOW,
        userMessage: 'Action saved for when connection is restored.'
      }
    );

    return queuedAction.id;
  }

  /**
   * Process offline queue
   */
  async processOfflineQueue() {
    if (this.isOffline || this.offlineQueue.length === 0) {
      return;
    }

    const queue = [...this.offlineQueue];
    this.offlineQueue = [];
    const processedActions = [];
    const failedActions = [];

    for (const action of queue) {
      try {
        await this.processQueuedAction(action);
        processedActions.push(action);
      } catch (error) {
        action.retries++;
        if (action.retries < action.maxRetries) {
          failedActions.push(action);
        } else {
          handleError(
            new Error(`Max retries exceeded for offline action: ${action.type}`),
            { context: 'offline_action_failed', actionId: action.id },
            { 
              showToast: true,
              severity: ERROR_SEVERITY.MEDIUM,
              userMessage: 'Some offline actions could not be completed.'
            }
          );
        }
      }
    }

    // Re-queue failed actions
    this.offlineQueue = failedActions;
    this.saveOfflineQueue();

    if (processedActions.length > 0) {
      handleError(
        new Error(`Processed ${processedActions.length} offline actions`),
        { context: 'offline_actions_processed', count: processedActions.length },
        { 
          showToast: true,
          severity: ERROR_SEVERITY.LOW,
          userMessage: `${processedActions.length} offline actions completed successfully.`
        }
      );
    }
  }

  /**
   * Process individual queued action
   */
  async processQueuedAction(action) {
    // This would be implemented based on specific action types
    // For now, we'll simulate processing
    
    switch (action.type) {
      case 'SCAN_UPLOAD':
        return this.processOfflineScanUpload(action);
      case 'SETTINGS_UPDATE':
        return this.processOfflineSettingsUpdate(action);
      case 'NOTIFICATION_READ':
        return this.processOfflineNotificationRead(action);
      default:
        throw new Error(`Unknown offline action type: ${action.type}`);
    }
  }

  /**
   * Process offline scan upload
   */
  async processOfflineScanUpload(action) {
    // Simulate scan upload processing
    // In a real implementation, this would retry the actual upload
    return new Promise((resolve) => {
      setTimeout(resolve, 1000);
    });
  }

  /**
   * Process offline settings update
   */
  async processOfflineSettingsUpdate(action) {
    // Simulate settings update
    return new Promise((resolve) => {
      setTimeout(resolve, 500);
    });
  }

  /**
   * Process offline notification read
   */
  async processOfflineNotificationRead(action) {
    // Simulate notification read
    return new Promise((resolve) => {
      setTimeout(resolve, 300);
    });
  }

  /**
   * Cache data for offline access
   */
  cacheData(key, data, expiry = this.cacheExpiry) {
    const cacheEntry = {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + expiry
    };

    this.offlineCache.set(key, cacheEntry);
    this.saveOfflineCache();
  }

  /**
   * Get cached data
   */
  getCachedData(key) {
    const cacheEntry = this.offlineCache.get(key);
    
    if (!cacheEntry) {
      return null;
    }

    if (Date.now() > cacheEntry.expiry) {
      this.offlineCache.delete(key);
      return null;
    }

    return cacheEntry.data;
  }

  /**
   * Get offline queue status
   */
  getQueueStatus() {
    return {
      total: this.offlineQueue.length,
      pending: this.offlineQueue.filter(action => action.status === 'pending').length,
      processing: this.offlineQueue.filter(action => action.status === 'processing').length,
      failed: this.offlineQueue.filter(action => action.status === 'failed').length,
      completed: this.offlineQueue.filter(action => action.status === 'completed').length
    };
  }

  /**
   * Clear offline queue
   */
  clearQueue() {
    this.offlineQueue = [];
    this.saveOfflineQueue();
    
    handleError(
      new Error('Offline queue cleared'),
      { context: 'queue_cleared' },
      { 
        showToast: true,
        severity: ERROR_SEVERITY.LOW,
        userMessage: 'Offline queue cleared.'
      }
    );
  }

  /**
   * Add offline mode callback
   */
  addCallback(callback) {
    this.offlineModeCallbacks.add(callback);
  }

  /**
   * Remove offline mode callback
   */
  removeCallback(callback) {
    this.offlineModeCallbacks.delete(callback);
  }

  /**
   * Notify callbacks
   */
  notifyCallbacks(event) {
    this.offlineModeCallbacks.forEach(callback => {
      try {
        callback(event, this.isOffline);
      } catch (error) {
        console.error('Error in offline mode callback:', error);
      }
    });
  }

  /**
   * Save offline queue to localStorage
   */
  saveOfflineQueue() {
    try {
      localStorage.setItem('offlineQueue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  /**
   * Load offline queue from localStorage
   */
  loadOfflineQueue() {
    try {
      const saved = localStorage.getItem('offlineQueue');
      if (saved) {
        this.offlineQueue = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
    }
  }

  /**
   * Save offline cache to localStorage
   */
  saveOfflineCache() {
    try {
      localStorage.setItem('offlineCache', JSON.stringify(Array.from(this.offlineCache.entries())));
    } catch (error) {
      console.error('Failed to save offline cache:', error);
    }
  }

  /**
   * Load offline cache from localStorage
   */
  loadOfflineCache() {
    try {
      const saved = localStorage.getItem('offlineCache');
      if (saved) {
        const entries = JSON.parse(saved);
        this.offlineCache = new Map(entries);
        
        // Clean expired entries
        for (const [key, entry] of this.offlineCache.entries()) {
          if (Date.now() > entry.expiry) {
            this.offlineCache.delete(key);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load offline cache:', error);
    }
  }

  /**
   * Generate unique action ID
   */
  generateActionId() {
    return `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get offline mode status
   */
  getStatus() {
    return {
      isOffline: this.isOffline,
      queueSize: this.offlineQueue.length,
      cacheSize: this.offlineCache.size,
      queueStatus: this.getQueueStatus()
    };
  }
}

// Create singleton instance
const offlineModeHandler = new OfflineModeHandler();
export default offlineModeHandler;