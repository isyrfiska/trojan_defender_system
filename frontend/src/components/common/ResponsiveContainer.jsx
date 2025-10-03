import React from 'react';
import { Box, Container, useMediaQuery, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';

// Discord-inspired responsive container with mobile-first design
const StyledContainer = styled(Container)(({ theme, variant, fullHeight }) => ({
  padding: theme.spacing(2),
  transition: 'all 0.2s ease',
  
  // Mobile-first responsive padding
  [theme.breakpoints.up('xs')]: {
    padding: theme.spacing(1, 2),
  },
  [theme.breakpoints.up('sm')]: {
    padding: theme.spacing(2, 3),
  },
  [theme.breakpoints.up('md')]: {
    padding: theme.spacing(3, 4),
  },
  [theme.breakpoints.up('lg')]: {
    padding: theme.spacing(4, 5),
  },
  
  // Full height option for mobile layouts
  ...(fullHeight && {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  }),
  
  // Variant styles
  ...(variant === 'dashboard' && {
    backgroundColor: theme.palette.mode === 'dark' ? '#36393f' : '#f6f6f6',
    borderRadius: theme.spacing(1),
    [theme.breakpoints.down('sm')]: {
      borderRadius: 0,
      backgroundColor: 'transparent',
    },
  }),
  
  ...(variant === 'form' && {
    maxWidth: '500px',
    margin: '0 auto',
    padding: theme.spacing(3),
    [theme.breakpoints.down('sm')]: {
      padding: theme.spacing(2, 1),
      maxWidth: '100%',
    },
  }),
  
  ...(variant === 'card' && {
    backgroundColor: theme.palette.background.paper,
    borderRadius: theme.spacing(1),
    boxShadow: theme.shadows[2],
    [theme.breakpoints.down('sm')]: {
      borderRadius: 0,
      boxShadow: 'none',
      borderBottom: `1px solid ${theme.palette.divider}`,
    },
  }),
}));

// Touch-friendly wrapper for interactive elements
const TouchWrapper = styled(Box)(({ theme }) => ({
  // Minimum touch target size (44px recommended)
  minHeight: '44px',
  minWidth: '44px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  
  // Touch feedback
  '&:active': {
    transform: 'scale(0.98)',
    transition: 'transform 0.1s ease',
  },
  
  // Focus styles for keyboard navigation
  '&:focus-visible': {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: '2px',
    borderRadius: theme.spacing(0.5),
  },
}));

// Responsive grid system
const ResponsiveGrid = styled(Box)(({ theme, columns = 1, gap = 2 }) => ({
  display: 'grid',
  gap: theme.spacing(gap),
  gridTemplateColumns: `repeat(${columns}, 1fr)`,
  
  // Responsive breakpoints
  [theme.breakpoints.down('sm')]: {
    gridTemplateColumns: '1fr',
    gap: theme.spacing(1),
  },
  [theme.breakpoints.up('sm')]: {
    gridTemplateColumns: columns <= 2 ? `repeat(${columns}, 1fr)` : 'repeat(2, 1fr)',
  },
  [theme.breakpoints.up('md')]: {
    gridTemplateColumns: `repeat(${Math.min(columns, 3)}, 1fr)`,
  },
  [theme.breakpoints.up('lg')]: {
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
  },
}));

// Mobile navigation safe area
const SafeAreaContainer = styled(Box)(({ theme }) => ({
  paddingTop: 'env(safe-area-inset-top)',
  paddingBottom: 'env(safe-area-inset-bottom)',
  paddingLeft: 'env(safe-area-inset-left)',
  paddingRight: 'env(safe-area-inset-right)',
  
  // Additional padding for mobile browsers
  [theme.breakpoints.down('sm')]: {
    paddingBottom: `calc(env(safe-area-inset-bottom) + ${theme.spacing(2)})`,
  },
}));

// Main responsive container component
const ResponsiveContainer = ({ 
  children, 
  variant = 'default',
  maxWidth = 'lg',
  fullHeight = false,
  disableGutters = false,
  ...props 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  return (
    <SafeAreaContainer>
      <StyledContainer
        maxWidth={maxWidth}
        variant={variant}
        fullHeight={fullHeight}
        disableGutters={disableGutters || isMobile}
        {...props}
      >
        {children}
      </StyledContainer>
    </SafeAreaContainer>
  );
};

// Mobile-optimized stack layout
export const MobileStack = ({ children, spacing = 2, ...props }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing(isMobile ? 1 : spacing),
        width: '100%',
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

// Touch-friendly button wrapper
export const TouchButton = ({ children, onClick, disabled, ...props }) => {
  return (
    <TouchWrapper
      component="button"
      onClick={onClick}
      disabled={disabled}
      sx={{
        border: 'none',
        background: 'transparent',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </TouchWrapper>
  );
};

// Responsive text that adjusts size based on screen
export const ResponsiveText = ({ 
  variant = 'body1', 
  mobileVariant, 
  children, 
  ...props 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const effectiveVariant = isMobile && mobileVariant ? mobileVariant : variant;
  
  return (
    <Box
      component="span"
      sx={{
        fontSize: theme.typography[effectiveVariant].fontSize,
        fontWeight: theme.typography[effectiveVariant].fontWeight,
        lineHeight: theme.typography[effectiveVariant].lineHeight,
        // Ensure text is readable on mobile
        [theme.breakpoints.down('sm')]: {
          fontSize: `max(${theme.typography[effectiveVariant].fontSize}, 16px)`,
        },
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

export { ResponsiveGrid, SafeAreaContainer, TouchWrapper };
export default ResponsiveContainer;