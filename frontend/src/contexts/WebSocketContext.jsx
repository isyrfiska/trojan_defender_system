import { createContext, useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useAlert } from '../hooks/useAlert';

export const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [threatEvents, setThreatEvents] = useState([]);
  const [threatStats, setThreatStats] = useState(null);
  const [recentThreats, setRecentThreats] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // disconnected, connecting, connected, error
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const wsRef = useRef(null);
  const threatIntelligenceWsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const { isAuthenticated, currentUser, token } = useAuth();
  const { error, warning, info, success } = useAlert();

  const connectWebSocket = useCallback(() => {
    if (!isAuthenticated || !currentUser || !token) {
      return;
    }

    setConnectionStatus('connecting');

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setConnectionStatus('connected');
      setReconnectAttempts(0);
      
      // Subscribe to channels
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'threat_updates'
      }));
      
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'system_notifications'
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      setConnectionStatus('disconnected');
      
      // Attempt to reconnect with exponential backoff
      const backoffDelay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      reconnectTimeoutRef.current = setTimeout(() => {
        if (isAuthenticated && currentUser) {
          setReconnectAttempts(prev => prev + 1);
          connectWebSocket();
        }
      }, backoffDelay);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setConnectionStatus('error');
      error('Connection error. Trying to reconnect...');
    };
  }, [isAuthenticated, currentUser, token, error, reconnectAttempts]);

  const connectThreatIntelligenceWebSocket = useCallback(() => {
    if (!isAuthenticated || !currentUser || !token) {
      return;
    }

    // Close existing connection if any
    if (threatIntelligenceWsRef.current) {
      threatIntelligenceWsRef.current.close();
    }

    const wsUrl = `ws://localhost:8000/ws/threat-intelligence/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    threatIntelligenceWsRef.current = ws;

    ws.onopen = () => {
      console.log('Threat Intelligence WebSocket connected');
      
      // Request initial stats
      ws.send(JSON.stringify({
        type: 'get_stats'
      }));
      
      // Request recent threats
      ws.send(JSON.stringify({
        type: 'get_recent_threats',
        limit: 20
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleThreatIntelligenceMessage(data);
      } catch (err) {
        console.error('Error parsing Threat Intelligence WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('Threat Intelligence WebSocket disconnected');
      
      // Attempt to reconnect after 10 seconds
      setTimeout(() => {
        if (isAuthenticated && currentUser) {
          connectThreatIntelligenceWebSocket();
        }
      }, 10000);
    };

    ws.onerror = (err) => {
      console.error('Threat Intelligence WebSocket error:', err);
    };
  }, [isAuthenticated, currentUser, token]);

  useEffect(() => {
    if (isAuthenticated && currentUser) {
      connectWebSocket();
      connectThreatIntelligenceWebSocket();
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        setConnected(false);
        setConnectionStatus('disconnected');
      }
      if (threatIntelligenceWsRef.current) {
        threatIntelligenceWsRef.current.close();
      }
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (threatIntelligenceWsRef.current) {
        threatIntelligenceWsRef.current.close();
      }
    };
  }, [isAuthenticated, currentUser, connectWebSocket, connectThreatIntelligenceWebSocket]);

  const handleWebSocketMessage = (data) => {
    setMessages((prev) => [...prev, data]);

    switch (data.type) {
      case 'pong':
        // Handle ping/pong for connection health
        break;
      case 'subscription_confirmed':
        console.log(`Subscribed to channel: ${data.channel}`);
        break;
      case 'scan_complete':
        if (data.threat_level && data.threat_level !== 'clean') {
          warning(`Scan complete: ${data.threat_count} threat(s) detected in ${data.file_name}`);
        } else {
          info(`Scan complete: ${data.file_name} is clean`);
        }
        break;
      case 'scan_status_update':
        info(`Scan ${data.status_display}: ${data.file_name}`);
        break;
      case 'threat_detected':
        warning(`Threat detected in ${data.file_name}: ${data.threat_name}`);
        setThreatEvents((prev) => [...prev, data]);
        break;
      case 'threat_event':
        setThreatEvents((prev) => [...prev, data]);
        break;
      case 'security_alert':
        error(`Security Alert: ${data.message}`);
        break;
      case 'system_notification':
        info(data.message);
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
        break;
    }
  };

  const handleThreatIntelligenceMessage = (data) => {
    switch (data.type) {
      case 'initial_stats':
      case 'stats_update':
        setThreatStats(data.data);
        break;
      case 'recent_threats':
        setRecentThreats(data.data);
        break;
      case 'threat_update':
        // Update threat stats when new threat data is available
        if (data.data.action === 'created') {
          success(`New threat detected: ${data.data.ip_address} (${data.data.country})`);
        }
        // Refresh stats
        if (threatIntelligenceWsRef.current && threatIntelligenceWsRef.current.readyState === WebSocket.OPEN) {
          threatIntelligenceWsRef.current.send(JSON.stringify({
            type: 'get_stats'
          }));
        }
        break;
      case 'new_threat_event':
        warning(`Threat event: ${data.data.description} from ${data.data.ip_address}`);
        setRecentThreats((prev) => [data.data, ...prev.slice(0, 19)]); // Keep only 20 most recent
        break;
      case 'error':
        console.error('Threat Intelligence WebSocket error:', data.message);
        break;
      default:
        console.log('Unknown Threat Intelligence WebSocket message type:', data.type);
        break;
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  };

  const sendThreatIntelligenceMessage = (message) => {
    if (threatIntelligenceWsRef.current && threatIntelligenceWsRef.current.readyState === WebSocket.OPEN) {
      threatIntelligenceWsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  };

  // Ping to keep connection alive
  useEffect(() => {
    const pingInterval = setInterval(() => {
      if (connected && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [connected]);

  const value = {
    connected,
    connectionStatus,
    messages,
    threatEvents,
    threatStats,
    recentThreats,
    reconnectAttempts,
    sendMessage,
    sendThreatIntelligenceMessage,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};