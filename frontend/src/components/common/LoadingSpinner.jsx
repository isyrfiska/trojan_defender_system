import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Typography,
  Backdrop,
  Skeleton,
  Card,
  CardContent,
  Grid,
  keyframes,
} from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';

// Discord-inspired loading animations
const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

const rotate = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const StyledCircularProgress = styled(CircularProgress)(({ theme }) => ({
  color: theme.palette.primary.main,
  animation: `${pulse} 2s ease-in-out infinite`,
  '& .MuiCircularProgress-circle': {
    strokeLinecap: 'round',
    filter: 'drop-shadow(0 0 8px rgba(88, 101, 242, 0.4))',
  },
}));

const LoadingText = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontWeight: theme.typography.fontWeightMedium,
  animation: `${pulse} 2s ease-in-out infinite 0.5s`,
  textAlign: 'center',
}));

const SkeletonBox = styled(Box)(({ theme, width = '100%', height = '20px' }) => ({
  width,
  height,
  backgroundColor: theme.palette.grey[800],
  borderRadius: theme.shape.borderRadius,
  background: `linear-gradient(90deg, ${theme.palette.grey[800]} 25%, ${theme.palette.grey[700]} 50%, ${theme.palette.grey[800]} 75%)`,
  backgroundSize: '200px 100%',
  animation: `${shimmer} 1.5s infinite linear`,
  marginBottom: theme.spacing(1),
}));

const DiscordSpinner = styled(Box)(({ theme }) => ({
  width: '40px',
  height: '40px',
  border: '3px solid transparent',
  borderTop: `3px solid ${theme.palette.primary.main}`,
  borderRight: `3px solid ${theme.palette.secondary.main}`,
  borderRadius: '50%',
  animation: `${rotate} 1s linear infinite`,
  filter: 'drop-shadow(0 0 8px rgba(88, 101, 242, 0.4))',
}));



const LoadingSpinner = ({
  message = 'Loading...',
  size = 40,
  fullScreen = false,
  overlay = false,
  color = 'primary',
  variant = 'circular', // 'circular', 'discord', 'skeleton'
}) => {
  const theme = useTheme();
  const isLight = theme.palette.mode === 'light';

  const LoadingContent = () => (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        p: 3,
      }}
    >
      {variant === 'skeleton' ? (
        <Box sx={{ width: '100%', maxWidth: 400 }}>
          <SkeletonBox height="24px" />
          <SkeletonBox height="20px" />
          <SkeletonBox height="20px" width="80%" />
          <SkeletonBox height="20px" width="60%" />
        </Box>
      ) : variant === 'discord' ? (
        <DiscordSpinner sx={{ width: size, height: size }} />
      ) : (
        <StyledCircularProgress size={size} color={color} />
      )}
      
      {message && variant !== 'skeleton' && (
        <LoadingText variant="body2">
          {message}
        </LoadingText>
      )}
    </Box>
  );

  if (fullScreen) {
    return (
      <Backdrop
        sx={{
          color: theme.palette.common.white,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: isLight ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.7)',
        }}
        open={true}
      >
        <LoadingContent />
      </Backdrop>
    );
  }

  if (overlay) {
    return (
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: isLight ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.6)',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <LoadingContent />
      </Box>
    );
  }

  return <LoadingContent />;
};

export default LoadingSpinner;