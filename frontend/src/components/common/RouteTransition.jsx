import React from 'react';
import { Box, Fade, Slide, Grow, Zoom } from '@mui/material';
import { useLocation } from 'react-router-dom';

const RouteTransition = ({ 
  children, 
  type = 'fade',
  duration = 300,
  direction = 'up',
  timeout = { enter: duration, exit: duration / 2 }
}) => {
  const location = useLocation();

  const getTransitionComponent = () => {
    switch (type) {
      case 'slide':
        return (
          <Slide
            direction={direction}
            in={true}
            timeout={timeout}
            mountOnEnter
            unmountOnExit
          >
            <Box>{children}</Box>
          </Slide>
        );
      
      case 'grow':
        return (
          <Grow
            in={true}
            timeout={timeout}
            style={{ transformOrigin: '0 0 0' }}
          >
            <Box>{children}</Box>
          </Grow>
        );
      
      case 'zoom':
        return (
          <Zoom
            in={true}
            timeout={timeout}
            style={{ transitionDelay: '100ms' }}
          >
            <Box>{children}</Box>
          </Zoom>
        );
      
      case 'fade':
      default:
        return (
          <Fade
            in={true}
            timeout={timeout}
          >
            <Box>{children}</Box>
          </Fade>
        );
    }
  };

  return (
    <Box
      key={location.pathname}
      sx={{
        width: '100%',
        height: '100%',
      }}
    >
      {getTransitionComponent()}
    </Box>
  );
};

export default RouteTransition;