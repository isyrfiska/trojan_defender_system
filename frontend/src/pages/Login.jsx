import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import {
  Avatar,
  FormControlLabel,
  Checkbox,
  Link as MuiLink,
  Paper,
  Box,
  Grid,
  Typography,
  Alert,
  Divider,
  Fade,
  useTheme,
} from '@mui/material';
import {
  LockOutlined as LockOutlinedIcon,
  Security as SecurityIcon,
  Fingerprint as FingerprintIcon,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useAlert } from '../hooks/useAlert';
import { PrimaryButton, EmailInput, PasswordInput, LoadingSpinner } from '../components/common';
import cybersecurityBg from '../assets/cybersecurity-bg.svg';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const { login, isAuthenticated } = useAuth();
  const { addAlert } = useAlert();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [showSecurityTip, setShowSecurityTip] = useState(false);

  // Get the intended destination from location state
  const from = location.state?.from?.pathname || '/dashboard';

  // Check if user is already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from);
    }
  }, [isAuthenticated, navigate, from]);

  // Load saved credentials if remember me was checked
  useEffect(() => {
    const savedEmail = localStorage.getItem('rememberedEmail');
    const savedRememberMe = localStorage.getItem('rememberMe') === 'true';
    
    if (savedEmail && savedRememberMe) {
      setFormData(prev => ({
        ...prev,
        email: savedEmail,
        rememberMe: savedRememberMe,
      }));
    }
    
    // Show security tip after a short delay
    const tipTimer = setTimeout(() => {
      setShowSecurityTip(true);
    }, 1500);
    
    return () => clearTimeout(tipTimer);
  }, []);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Clear error when user starts typing
    setErrors(prevErrors => {
      if (prevErrors[name]) {
        return {
          ...prevErrors,
          [name]: '',
        };
      }
      return prevErrors;
    });
  }, []);

  const validateForm = useCallback(() => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setErrors({});

    try {
        // Increment login attempts counter
        setLoginAttempts(prev => prev + 1);
        
        // Save email if remember me is checked
        if (formData.rememberMe) {
            localStorage.setItem('rememberedEmail', formData.email);
            localStorage.setItem('rememberMe', 'true');
        } else {
            localStorage.removeItem('rememberedEmail');
            localStorage.removeItem('rememberMe');
        }
        
        // Call login function from auth context
        const result = await login(formData.email, formData.password);
        
        if (result.success) {
            // Reset login attempts on successful login
            setLoginAttempts(0);
            localStorage.removeItem('loginAttempts');
            
            // Show success message
            addAlert('Login successful! Welcome back.', 'success');
            
            // Navigate to intended destination
            navigate(from, { replace: true });
        } else {
            // Show appropriate error message
            const errorMessage = result.error || 'Login failed. Please check your credentials and try again.';
            addAlert(errorMessage, 'error');
            
            // Add specific field error if provided in the response
            if (result.fieldErrors) {
                setErrors(result.fieldErrors);
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        addAlert('An unexpected error occurred. Please try again later.', 'error');
    } finally {
        setLoading(false);
    }
};
  return (
    <Grid container component="main" sx={{ height: '100vh' }}>
      <Grid
        item
        xs={false}
        sm={4}
        md={7}
        sx={{
          backgroundImage: `url(${cybersecurityBg})`,
          backgroundRepeat: 'no-repeat',
          backgroundColor: theme.palette.mode === 'dark' ? '#121212' : '#f5f5f5',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          display: { xs: 'none', sm: 'block' },
          position: 'relative',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            bottom: 40,
            left: 40,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            p: 2,
            borderRadius: 1,
            maxWidth: '80%',
          }}
        >
          <Typography variant="h6" gutterBottom>
            Trojan Defender Security Platform
          </Typography>
          <Typography variant="body2">
            Advanced threat detection and protection for your enterprise
          </Typography>
        </Box>
      </Grid>
      <Grid item xs={12} sm={8} md={5} component={Paper} elevation={6} square>
        <Box
          sx={{
            my: 8,
            mx: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: 'calc(100% - 64px)',
            position: 'relative',
            zIndex: 1
          }}
        >
          <Avatar sx={{ m: 1, bgcolor: 'primary.main', width: 56, height: 56 }} aria-hidden="true">
            <LockOutlinedIcon fontSize="large" />
          </Avatar>
          <Typography 
            component="h1" 
            variant="h4"
            id="login-title"
            sx={{ textAlign: 'center', mb: 1, fontWeight: 600 }}
          >
            Sign in
          </Typography>
          <Typography 
            variant="subtitle1" 
            color="text.secondary"
            sx={{ mb: 3, textAlign: 'center' }}
          >
            Access your Trojan Defender dashboard
          </Typography>
          
          {/* Security Tip Alert */}
          <Fade in={showSecurityTip}>
            <Alert 
              severity="info" 
              icon={<SecurityIcon />}
              sx={{ 
                mb: 3, 
                width: '100%',
                '& .MuiAlert-message': { width: '100%' }
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Security Tip</Typography>
              <Typography variant="body2">
                Use a strong, unique password and enable two-factor authentication for enhanced security.
              </Typography>
            </Alert>
          </Fade>
          
          <Box 
            component="form" 
            noValidate 
            onSubmit={handleSubmit} 
            sx={{ mt: 1, width: '100%' }}
            role="form"
            aria-labelledby="login-title"
          >
            <EmailInput
              required
              id="email"
              name="email"
              autoComplete="email"
              autoFocus
              value={formData.email}
              onChange={handleChange}
              error={!!errors.email}
              helperText={errors.email}
              sx={{ mb: 2 }}
              aria-describedby={errors.email ? "email-error" : undefined}
              inputProps={{
                'aria-label': 'Email address',
                'aria-required': 'true',
                'aria-invalid': !!errors.email
              }}
            />
            <PasswordInput
              required
              name="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              error={!!errors.password}
              helperText={errors.password}
              sx={{ mb: 2 }}
              aria-describedby={errors.password ? "password-error" : undefined}
              inputProps={{
                'aria-label': 'Password',
                'aria-required': 'true',
                'aria-invalid': !!errors.password
              }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  name="rememberMe"
                  color="primary"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  inputProps={{
                    'aria-label': 'Remember me for future logins'
                  }}
                />
              }
              label="Remember me"
              sx={{ mb: 2 }}
            />
            <PrimaryButton
              type="submit"
              fullWidth
              loading={loading}
              size="large"
              disabled={loading}
              aria-describedby={loading ? "login-loading" : undefined}
              sx={{ 
                mt: 2, 
                mb: 3,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
              }}
              startIcon={!loading && <FingerprintIcon />}
            >
              {loading ? 'Signing in...' : 'Sign In Securely'}
            </PrimaryButton>
            
            {loading && (
              <Box 
                id="login-loading" 
                sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}
                role="status" 
                aria-live="polite"
              >
                <LoadingSpinner 
                  size={24} 
                  variant="discord"
                  message="Authenticating..."
                />
              </Box>
            )}
            
            <Divider sx={{ my: 2 }}>
              <Typography variant="body2" color="text.secondary">
                OR
              </Typography>
            </Divider>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <MuiLink 
                  component={Link} 
                  to="/forgot-password" 
                  variant="body2"
                  aria-label="Forgot your password? Click to reset"
                  sx={{ 
                    display: 'block',
                    textAlign: { xs: 'center', sm: 'left' },
                    fontWeight: 500,
                  }}
                >
                  Forgot password?
                </MuiLink>
              </Grid>
              <Grid item xs={12} sm={6}>
                <MuiLink 
                  component={Link} 
                  to="/register" 
                  variant="body2"
                  aria-label="Don't have an account? Click to sign up"
                  sx={{ 
                    display: 'block',
                    textAlign: { xs: 'center', sm: 'right' },
                    fontWeight: 500,
                  }}
                >
                  Create an account
                </MuiLink>
              </Grid>
            </Grid>
            
            {/* Login attempts warning */}
            {loginAttempts > 2 && (
              <Alert 
                severity="warning" 
                sx={{ mt: 3 }}
              >
                Multiple failed login attempts detected. Please verify your credentials or reset your password.
              </Alert>
            )}
          </Box>
        </Box>
      </Grid>
    </Grid>
  );
};

export default Login;