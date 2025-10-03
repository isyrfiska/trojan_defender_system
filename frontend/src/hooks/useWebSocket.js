import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';
import { useAlert } from './useAlert';

const useWebSocket = (endpoint = '/ws/threatmap/', options = {}) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  const { token } = useAuth();
  const { showAlert } = useAlert();
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = options.maxReconnectAttempts || 5;
  const reconnectInterval = options.reconnectInterval || 3000;

  // Message handlers
  const messageHandlersRef = useRef(new Map());

  // Add message handler
  const addMessageHandler = useCallback((type, handler) => {
    if (!messageHandlersRef.current.has(type)) {
      messageHandlersRef.current.set(type, new Set());
    }
    messageHandlersRef.current.get(type).add(handler);

    // Return cleanup function
    return () => {
      const handlers = messageHandlersRef.current.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(type);
        }
      }
    };
  }, []);

  // Remove message handler
  const removeMessageHandler = useCallback((type, handler) => {
    const handlers = messageHandlersRef.current.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        messageHandlersRef.current.delete(type);
      }
    }
  }, []);

  // Send message
  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      try {
        socket.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        setConnectionError(error.message);
        return false;
      }
    }
    return false;
  }, [socket, isConnected]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!token) {
      console.warn('No authentication token available for WebSocket connection');
      return;
    }

    try {
      // Create WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host.replace(':3001', ':8000'); // Adjust for dev server
      const wsUrl = `${protocol}//${host}${endpoint}`;

      console.log('Connecting to WebSocket:', wsUrl);

      // Create WebSocket connection
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;

        // Send authentication
        ws.send(JSON.stringify({
          type: 'auth',
          token: token
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);

          // Handle different message types
          const handlers = messageHandlersRef.current.get(data.type);
          if (handlers) {
            handlers.forEach(handler => {
              try {
                handler(data);
              } catch (error) {
                console.error('Error in message handler:', error);
              }
            });
          }

          // Handle specific message types
          switch (data.type) {
            case 'error':
              console.error('WebSocket error:', data.message);
              setConnectionError(data.message);
              if (showAlert) {
                showAlert(data.message, 'error');
              }
              break;

            case 'threat_alert':
              if (showAlert) {
                showAlert(`Critical threat detected: ${data.data.threat_type}`, 'warning');
              }
              break;

            case 'connection_confirmed':
              console.log('WebSocket connection confirmed');
              break;

            default:
              // Handle other message types through registered handlers
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setSocket(null);

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Maximum reconnection attempts reached');
          if (showAlert) {
            showAlert('Lost connection to real-time updates', 'warning');
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection error');
      };

      setSocket(ws);
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionError(error.message);
    }
  }, [token, endpoint, maxReconnectAttempts, reconnectInterval, showAlert]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socket) {
      socket.close(1000, 'Manual disconnect');
    }

    setSocket(null);
    setIsConnected(false);
    setConnectionError(null);
    reconnectAttemptsRef.current = 0;
  }, [socket]);

  // Subscribe to threat updates with filters
  const subscribeToThreats = useCallback((filters = {}) => {
    return sendMessage({
      type: 'subscribe_filters',
      filters: filters
    });
  }, [sendMessage]);

  // Request threat data
  const requestThreatData = useCallback((filters = {}) => {
    return sendMessage({
      type: 'get_threats',
      filters: filters
    });
  }, [sendMessage]);

  // Effect to handle connection
  useEffect(() => {
    if (token && options.autoConnect !== false) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect, options.autoConnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    socket,
    isConnected,
    lastMessage,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    addMessageHandler,
    removeMessageHandler,
    subscribeToThreats,
    requestThreatData,
    reconnectAttempts: reconnectAttemptsRef.current,
    maxReconnectAttempts,
  };
};

// Specialized hook for threat map WebSocket
export const useThreatMapWebSocket = (options = {}) => {
  const [threatData, setThreatData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const webSocket = useWebSocket('/ws/threatmap/', {
    autoConnect: true,
    ...options
  });

  // Handle threat data updates
  useEffect(() => {
    const handleThreatData = (data) => {
      setThreatData(data.data || []);
      setLastUpdate(data.timestamp);
      setIsLoading(false);
    };

    const handleThreatUpdate = (data) => {
      setThreatData(prevData => {
        // Add new threat or update existing one
        const existingIndex = prevData.findIndex(threat => threat.id === data.data.id);
        if (existingIndex >= 0) {
          const newData = [...prevData];
          newData[existingIndex] = data.data;
          return newData;
        } else {
          return [data.data, ...prevData];
        }
      });
      setLastUpdate(data.timestamp);
    };

    const handleInitialData = (data) => {
      setThreatData(data.data || []);
      setLastUpdate(data.timestamp);
      setIsLoading(false);
    };

    // Register message handlers
    const cleanupHandlers = [
      webSocket.addMessageHandler('threat_data', handleThreatData),
      webSocket.addMessageHandler('threat_update', handleThreatUpdate),
      webSocket.addMessageHandler('initial_data', handleInitialData),
    ];

    return () => {
      cleanupHandlers.forEach(cleanup => cleanup());
    };
  }, [webSocket]);

  // Subscribe to threats with filters
  const subscribeWithFilters = useCallback((filters) => {
    setIsLoading(true);
    return webSocket.subscribeToThreats(filters);
  }, [webSocket]);

  // Request fresh threat data
  const refreshThreatData = useCallback((filters) => {
    setIsLoading(true);
    return webSocket.requestThreatData(filters);
  }, [webSocket]);

  return {
    ...webSocket,
    threatData,
    isLoading,
    lastUpdate,
    subscribeWithFilters,
    refreshThreatData,
  };
};

export default useWebSocket;