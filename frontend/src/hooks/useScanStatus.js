import { useState, useEffect, useCallback } from 'react';
import useWebSocket from './useWebSocket';
import scanService from '../services/scanService';

/**
 * Custom hook for tracking scan status in real-time
 * @param {string} scanId - The ID of the scan to track
 * @returns {object} Scan status information and utility functions
 */
export const useScanStatus = (scanId) => {
  const [status, setStatus] = useState('pending');
  const [threatLevel, setThreatLevel] = useState('clean');
  const [threatCount, setThreatCount] = useState(0);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { connected, sendMessage } = useWebSocket();

  // Fetch initial scan status
  useEffect(() => {
    if (!scanId) return;

    const fetchScanStatus = async () => {
      try {
        setLoading(true);
        const response = await scanService.getScanStatus(scanId);
        const data = response.data;
        
        setStatus(data.status);
        setThreatLevel(data.threat_level);
        setThreatCount(data.threat_count || 0);
        setProgress(data.status === 'completed' ? 100 : 50); // Set progress based on status
      } catch (err) {
        console.error('Error fetching scan status:', err);
        setError('Failed to fetch scan status');
      } finally {
        setLoading(false);
      }
    };

    fetchScanStatus();
  }, [scanId]);

  // Subscribe to WebSocket updates for this scan
  useEffect(() => {
    if (!connected || !scanId) return;

    // Subscribe to scan updates
    const subscribeMessage = {
      type: 'subscribe_scan',
      scan_id: scanId
    };
    sendMessage(subscribeMessage);

    return () => {
      // Unsubscribe when component unmounts
      const unsubscribeMessage = {
        type: 'unsubscribe_scan',
        scan_id: scanId
      };
      sendMessage(unsubscribeMessage);
    };
  }, [connected, scanId, sendMessage]);

  // Handle WebSocket messages for scan updates
  const handleScanUpdate = useCallback((data) => {
    if (data.scan_id !== scanId) return;

    setStatus(data.status);
    if (data.threat_level) setThreatLevel(data.threat_level);
    if (data.threat_count !== undefined) setThreatCount(data.threat_count);
    
    // Update progress based on status
    if (data.status === 'scanning') setProgress(50);
    if (data.status === 'completed') setProgress(100);
  }, [scanId]);

  // Refresh scan status manually
  const refreshStatus = useCallback(async () => {
    if (!scanId) return;
    
    try {
      setLoading(true);
      const response = await scanService.getScanStatus(scanId);
      const data = response.data;
      
      setStatus(data.status);
      setThreatLevel(data.threat_level);
      setThreatCount(data.threat_count || 0);
      setProgress(data.status === 'completed' ? 100 : 50);
    } catch (err) {
      console.error('Error refreshing scan status:', err);
      setError('Failed to refresh scan status');
    } finally {
      setLoading(false);
    }
  }, [scanId]);

  return {
    status,
    threatLevel,
    threatCount,
    progress,
    loading,
    error,
    refreshStatus
  };
};