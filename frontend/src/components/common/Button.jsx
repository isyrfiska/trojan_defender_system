import React from 'react';
import { Button as MuiButton, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';

// Custom styled button with cyberpunk theme integration
const StyledButton = styled(MuiButton)(({ theme, variant, size, color }) => ({
  // Base styles from design system
  fontFamily: 'var(--font-family-primary)',
  fontWeight: 'var(--font-weight-medium)',
  letterSpacing: 'var(--letter-spacing-wide)',
  borderRadius: 'var(--radius-md)',
  textTransform: 'none',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 'var(--space-2)',
  position: 'relative',
  overflow: 'hidden',
  
  // Cyberpunk glow effect base
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(45deg, transparent 30%, rgba(0, 255, 255, 0.1) 50%, transparent 70%)',
    transform: 'translateX(-100%)',
    transition: 'transform 0.6s ease',
    zIndex: 0,
  },
  
  '& > *': {
    position: 'relative',
    zIndex: 1,
  },
  
  // Size variants
  ...(size === 'small' && {
    height: '2rem', // 32px
    padding: '0 var(--space-3)',
    fontSize: 'var(--font-size-sm)',
  }),
  ...(size === 'medium' && {
    height: '2.5rem', // 40px
    padding: '0 var(--space-4)',
    fontSize: 'var(--font-size-base)',
  }),
  ...(size === 'large' && {
    height: '3rem', // 48px
    padding: '0 var(--space-6)',
    fontSize: 'var(--font-size-lg)',
  }),
  
  // Variant-specific cyberpunk styling
  ...(variant === 'contained' && {
    border: '1px solid transparent',
    backgroundImage: `linear-gradient(${theme.palette.background.paper}, ${theme.palette.background.paper}), 
                      linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    backgroundOrigin: 'border-box',
    backgroundClip: 'padding-box, border-box',
    
    '&:hover': {
      transform: 'translateY(-2px) scale(1.02)',
      boxShadow: `0 8px 25px -8px ${theme.palette.primary.main}40, 
                  0 0 20px ${theme.palette.primary.main}30`,
      '&::before': {
        transform: 'translateX(100%)',
      },
    },
  }),
  
  ...(variant === 'outlined' && {
    border: `2px solid ${theme.palette.primary.main}`,
    background: 'transparent',
    
    '&:hover': {
      transform: 'translateY(-1px)',
      boxShadow: `0 0 20px ${theme.palette.primary.main}50, 
                  inset 0 0 20px ${theme.palette.primary.main}10`,
      borderColor: theme.palette.primary.light,
      '&::before': {
        transform: 'translateX(100%)',
      },
    },
  }),
  
  ...(variant === 'text' && {
    background: 'transparent',
    
    '&:hover': {
      background: `${theme.palette.primary.main}10`,
      textShadow: `0 0 8px ${theme.palette.primary.main}80`,
      '&::before': {
        transform: 'translateX(100%)',
      },
    },
  }),
  
  // Enhanced hover effects
  '&:hover': {
    '&::after': {
      content: '""',
      position: 'absolute',
      top: '50%',
      left: '50%',
      width: '0',
      height: '0',
      background: `radial-gradient(circle, ${theme.palette.primary.main}20 0%, transparent 70%)`,
      transform: 'translate(-50%, -50%)',
      animation: 'pulse 0.6s ease-out',
      zIndex: 0,
    },
  },
  
  // Focus styles with cyberpunk glow
  '&:focus-visible': {
    outline: 'none',
    boxShadow: `0 0 0 3px ${theme.palette.primary.main}50, 
                0 0 20px ${theme.palette.primary.main}30`,
  },
  
  // Disabled state
  '&:disabled': {
    transform: 'none',
    boxShadow: 'none',
    opacity: 0.4,
    cursor: 'not-allowed',
    '&::before': {
      display: 'none',
    },
  },
  
  // Keyframe animations
  '@keyframes pulse': {
    '0%': {
      width: '0',
      height: '0',
    },
    '100%': {
      width: '200px',
      height: '200px',
    },
  },
}));

const Button = ({
  children,
  variant = 'contained',
  size = 'medium',
  color = 'primary',
  loading = false,
  disabled = false,
  startIcon,
  endIcon,
  fullWidth = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      color={color}
      disabled={disabled || loading}
      startIcon={loading ? null : startIcon}
      endIcon={loading ? null : endIcon}
      fullWidth={fullWidth}
      onClick={onClick}
      type={type}
      className={`btn ${className}`}
      {...props}
    >
      {loading && (
        <CircularProgress
          size={size === 'small' ? 16 : size === 'large' ? 24 : 20}
          color="inherit"
          sx={{ mr: 1 }}
        />
      )}
      {children}
    </StyledButton>
  );
};

// Enhanced predefined button variants with cyberpunk styling
export const PrimaryButton = (props) => (
  <Button variant="contained" color="primary" {...props} />
);

export const SecondaryButton = (props) => (
  <Button variant="contained" color="secondary" {...props} />
);

export const OutlineButton = (props) => (
  <Button variant="outlined" color="primary" {...props} />
);

export const TextButton = (props) => (
  <Button variant="text" color="primary" {...props} />
);

export const SuccessButton = (props) => (
  <Button variant="contained" color="success" {...props} />
);

export const ErrorButton = (props) => (
  <Button variant="contained" color="error" {...props} />
);

export const WarningButton = (props) => (
  <Button variant="contained" color="warning" {...props} />
);

// New cyberpunk-specific button variants
export const NeonButton = (props) => (
  <Button 
    variant="outlined" 
    color="primary" 
    sx={{
      borderColor: 'primary.main',
      color: 'primary.main',
      textShadow: '0 0 8px currentColor',
      '&:hover': {
        boxShadow: '0 0 20px currentColor, inset 0 0 20px rgba(0, 255, 255, 0.1)',
        borderColor: 'primary.light',
      }
    }}
    {...props} 
  />
);

export const GlowButton = (props) => (
  <Button 
    variant="contained" 
    color="primary"
    sx={{
      boxShadow: '0 0 20px rgba(0, 255, 255, 0.3)',
      '&:hover': {
        boxShadow: '0 0 30px rgba(0, 255, 255, 0.5), 0 0 60px rgba(0, 255, 255, 0.2)',
      }
    }}
    {...props} 
  />
);

export default Button;