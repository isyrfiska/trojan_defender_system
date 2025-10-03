import { createContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [lastLoginAttempt, setLastLoginAttempt] = useState(null);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Set axios default headers
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Get user data if token exists
      const userData = localStorage.getItem('userData');
      if (userData) {
        try {
          const parsedUser = JSON.parse(userData);
          setCurrentUser(parsedUser);
          setIsAuthenticated(true);
        } catch (e) {
          console.error('Error parsing user data:', e);
          // Invalid user data, clear storage
          localStorage.removeItem('token');
          localStorage.removeItem('userData');
          setCurrentUser(null);
          setIsAuthenticated(false);
        }
      } else {
        // If we have a token but no user data, validate the token with the server
        const validateToken = async () => {
          try {
            const response = await axios.get('/api/auth/profile/');
            if (response.data) {
              localStorage.setItem('userData', JSON.stringify(response.data));
              setCurrentUser(response.data);
              setIsAuthenticated(true);
            }
          } catch (error) {
            console.error('Token validation failed:', error);
            // Token is invalid, clear it
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
            setCurrentUser(null);
            setIsAuthenticated(false);
          }
        };
        validateToken();
      }
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      // Clear auth data
      localStorage.removeItem('token');
      localStorage.removeItem('userData');
      localStorage.removeItem('rememberedEmail');
      localStorage.removeItem('rememberMe');
      
      // Clear axios headers
      delete axios.defaults.headers.common['Authorization'];
      
      // Reset state
      setCurrentUser(null);
      setIsAuthenticated(false);
      
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  }, []);

  // Login function
  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    
    try {
      // Record login attempt time and count
      const now = new Date();
      setLastLoginAttempt(now);
      setLoginAttempts(prev => prev + 1);
      
      // Check for too many login attempts (rate limiting)
      if (loginAttempts > 5 && lastLoginAttempt && (now - lastLoginAttempt) < 300000) {
        throw new Error('Too many login attempts. Please try again later.');
      }
      
      // Make API call to login endpoint
      const response = await axios.post('/api/auth/login/', { email, password });
      
      if (response.data && response.data.access) {
        try {
          // Store token and user data
          localStorage.setItem('token', response.data.access);
          localStorage.setItem('refreshToken', response.data.refresh);
          
          // Make sure user data is valid before storing
          const userData = response.data.user || {};
          if (!userData.id) {
            throw new Error('Invalid user data received');
          }
          
          localStorage.setItem('userData', JSON.stringify(userData));
          
          // Set axios default headers
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
          
          // Update state
          setCurrentUser(userData);
          setIsAuthenticated(true);
          setLoginAttempts(0);
          
          return { success: true, user: userData };
        } catch (storageError) {
          console.error('Error storing credentials:', storageError);
          throw new Error('Failed to save login information');
        }
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.message || err.message || 'Authentication failed';
      setError(errorMessage);
      setRetryCount(prev => prev + 1);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    setLoading(true);
    setError(null);
    
    try {
      // Make API call to register endpoint
      const response = await axios.post('/api/auth/register/', userData);
      
      if (response.data && response.data.email) {
        return { success: true, data: response.data };
      } else {
        throw new Error('Registration failed');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.message || err.message || 'Registration failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
    setRetryCount(0);
  }, []);

  const value = {
    currentUser,
    isAuthenticated,
    loading,
    error,
    retryCount,
    login,
    logout,
    register,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};