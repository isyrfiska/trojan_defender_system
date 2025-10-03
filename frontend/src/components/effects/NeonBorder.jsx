import React from 'react';
import { styled, keyframes } from '@mui/material/styles';
import { Box } from '@mui/material';

// Neon glow animation
const neonGlow = keyframes`
  0%, 100% {
    box-shadow: 
      0 0 5px currentColor,
      0 0 10px currentColor,
      0 0 15px currentColor,
      0 0 20px currentColor;
  }
  50% {
    box-shadow: 
      0 0 2px currentColor,
      0 0 5px currentColor,
      0 0 8px currentColor,
      0 0 12px currentColor;
  }
`;

// Pulsing border animation
const borderPulse = keyframes`
  0%, 100% {
    border-color: currentColor;
    opacity: 1;
  }
  50% {
    border-color: transparent;
    opacity: 0.7;
  }
`;

// Rotating border animation
const rotateBorder = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

// Styled container for neon border effects
const NeonContainer = styled(Box)(({ 
  theme, 
  variant = 'glow', 
  color = 'primary', 
  intensity = 'medium',
  animated = false,
  borderRadius = 'var(--radius-md)'
}) => {
  const colorValue = theme.palette[color]?.main || color;
  
  return {
    position: 'relative',
    borderRadius,
    color: colorValue,
    
    // Base neon glow variant
    ...(variant === 'glow' && {
      border: `2px solid ${colorValue}`,
      boxShadow: `
        0 0 5px ${colorValue}40,
        0 0 10px ${colorValue}30,
        0 0 15px ${colorValue}20,
        inset 0 0 5px ${colorValue}10
      `,
      
      ...(animated && {
        animation: `${neonGlow} 2s ease-in-out infinite alternate`,
      }),
      
      '&:hover': {
        boxShadow: `
          0 0 8px ${colorValue}60,
          0 0 16px ${colorValue}40,
          0 0 24px ${colorValue}30,
          inset 0 0 8px ${colorValue}20
        `,
      },
    }),
    
    // Pulsing border variant
    ...(variant === 'pulse' && {
      border: `2px solid ${colorValue}`,
      
      ...(animated && {
        animation: `${borderPulse} 1.5s ease-in-out infinite`,
      }),
      
      '&:hover': {
        boxShadow: `0 0 15px ${colorValue}50`,
      },
    }),
    
    // Double border variant
    ...(variant === 'double' && {
      border: `1px solid ${colorValue}`,
      
      '&::before': {
        content: '""',
        position: 'absolute',
        top: '-4px',
        left: '-4px',
        right: '-4px',
        bottom: '-4px',
        border: `1px solid ${colorValue}80`,
        borderRadius,
        zIndex: -1,
      },
      
      '&:hover': {
        boxShadow: `
          0 0 10px ${colorValue}40,
          inset 0 0 10px ${colorValue}20
        `,
        
        '&::before': {
          boxShadow: `0 0 15px ${colorValue}30`,
        },
      },
    }),
    
    // Rotating border variant
    ...(variant === 'rotate' && {
      '&::before': {
        content: '""',
        position: 'absolute',
        top: '-2px',
        left: '-2px',
        right: '-2px',
        bottom: '-2px',
        background: `conic-gradient(from 0deg, transparent, ${colorValue}, transparent)`,
        borderRadius,
        zIndex: -1,
        
        ...(animated && {
          animation: `${rotateBorder} 3s linear infinite`,
        }),
      },
      
      '&::after': {
        content: '""',
        position: 'absolute',
        top: '0',
        left: '0',
        right: '0',
        bottom: '0',
        background: theme.palette.background.default,
        borderRadius: `calc(${borderRadius} - 2px)`,
        zIndex: -1,
      },
    }),
    
    // Intensity variations
    ...(intensity === 'low' && {
      filter: 'brightness(0.7)',
    }),
    
    ...(intensity === 'high' && {
      filter: 'brightness(1.3) saturate(1.2)',
    }),
  };
});

const NeonBorder = ({ 
  children, 
  variant = 'glow', 
  color = 'primary', 
  intensity = 'medium',
  animated = false,
  borderRadius = 'var(--radius-md)',
  sx = {},
  ...props 
}) => {
  return (
    <NeonContainer
      variant={variant}
      color={color}
      intensity={intensity}
      animated={animated}
      borderRadius={borderRadius}
      sx={sx}
      {...props}
    >
      {children}
    </NeonContainer>
  );
};

export default NeonBorder;