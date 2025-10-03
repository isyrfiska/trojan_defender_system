import React from 'react';
import { styled, keyframes } from '@mui/material/styles';
import { Typography } from '@mui/material';

// Glitch animation keyframes
const glitch = keyframes`
  0% {
    transform: translate(0);
  }
  20% {
    transform: translate(-2px, 2px);
  }
  40% {
    transform: translate(-2px, -2px);
  }
  60% {
    transform: translate(2px, 2px);
  }
  80% {
    transform: translate(2px, -2px);
  }
  100% {
    transform: translate(0);
  }
`;

const glitchBefore = keyframes`
  0% {
    clip-path: inset(40% 0 61% 0);
  }
  20% {
    clip-path: inset(92% 0 1% 0);
  }
  40% {
    clip-path: inset(43% 0 1% 0);
  }
  60% {
    clip-path: inset(25% 0 58% 0);
  }
  80% {
    clip-path: inset(54% 0 7% 0);
  }
  100% {
    clip-path: inset(58% 0 43% 0);
  }
`;

const glitchAfter = keyframes`
  0% {
    clip-path: inset(25% 0 58% 0);
  }
  20% {
    clip-path: inset(6% 0 87% 0);
  }
  40% {
    clip-path: inset(71% 0 29% 0);
  }
  60% {
    clip-path: inset(25% 0 58% 0);
  }
  80% {
    clip-path: inset(80% 0 15% 0);
  }
  100% {
    clip-path: inset(50% 0 31% 0);
  }
`;

// Styled component for glitch text effect
const GlitchContainer = styled('div')(({ theme, intensity = 'medium', trigger = 'hover' }) => ({
  position: 'relative',
  display: 'inline-block',
  
  // Base glitch effect
  ...(trigger === 'always' && {
    animation: `${glitch} 0.3s infinite linear alternate-reverse`,
  }),
  
  // Hover-triggered glitch
  ...(trigger === 'hover' && {
    '&:hover': {
      animation: `${glitch} 0.3s infinite linear alternate-reverse`,
      
      '&::before, &::after': {
        content: 'attr(data-text)',
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: theme.palette.background.default,
      },
      
      '&::before': {
        animation: `${glitchBefore} 0.3s infinite linear alternate-reverse`,
        color: theme.palette.primary.main,
        zIndex: -1,
      },
      
      '&::after': {
        animation: `${glitchAfter} 0.3s infinite linear alternate-reverse`,
        color: theme.palette.secondary.main,
        zIndex: -2,
      },
    },
  }),
  
  // Intensity variations
  ...(intensity === 'low' && {
    '&:hover': {
      animationDuration: '0.5s',
    },
  }),
  
  ...(intensity === 'high' && {
    '&:hover': {
      animationDuration: '0.15s',
      '&::before, &::after': {
        animationDuration: '0.15s',
      },
    },
  }),
}));

const GlitchText = ({ 
  children, 
  variant = 'h6', 
  intensity = 'medium', 
  trigger = 'hover',
  component,
  sx = {},
  ...props 
}) => {
  return (
    <GlitchContainer 
      intensity={intensity} 
      trigger={trigger}
      data-text={typeof children === 'string' ? children : ''}
    >
      <Typography
        variant={variant}
        component={component}
        sx={{
          fontFamily: 'var(--font-family-primary)',
          textShadow: trigger === 'always' ? '0 0 10px currentColor' : 'none',
          ...sx,
        }}
        {...props}
      >
        {children}
      </Typography>
    </GlitchContainer>
  );
};

export default GlitchText;