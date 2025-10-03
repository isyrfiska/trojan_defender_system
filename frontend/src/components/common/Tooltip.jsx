import React, { useState } from 'react';
import { Tooltip as MuiTooltip, Fade, Zoom } from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledTooltip = styled(({ className, ...props }) => (
  <MuiTooltip {...props} classes={{ popper: className }} />
))(({ theme }) => {
  const isLight = theme.palette.mode === 'light';
  const tooltipBg = isLight ? theme.palette.grey[800] : theme.palette.grey[900];
  const tooltipBorder = isLight ? theme.palette.grey[600] : theme.palette.grey[700];
  
  return {
    '& .MuiTooltip-tooltip': {
      backgroundColor: tooltipBg,
      color: theme.palette.common.white,
      fontSize: theme.typography.pxToRem(12),
      fontWeight: theme.typography.fontWeightMedium,
      padding: theme.spacing(1, 1.5),
      borderRadius: theme.shape.borderRadius,
      border: `1px solid ${tooltipBorder}`,
      boxShadow: theme.shadows[8],
      maxWidth: 300,
      '&::before': {
        content: '""',
        position: 'absolute',
        width: 0,
        height: 0,
        border: '6px solid transparent',
      },
    },
    '& .MuiTooltip-tooltipPlacementTop::before': {
      borderTopColor: tooltipBg,
      bottom: '-12px',
      left: '50%',
      transform: 'translateX(-50%)',
    },
    '& .MuiTooltip-tooltipPlacementBottom::before': {
      borderBottomColor: tooltipBg,
      top: '-12px',
      left: '50%',
      transform: 'translateX(-50%)',
    },
    '& .MuiTooltip-tooltipPlacementLeft::before': {
      borderLeftColor: tooltipBg,
      right: '-12px',
      top: '50%',
      transform: 'translateY(-50%)',
    },
    '& .MuiTooltip-tooltipPlacementRight::before': {
      borderRightColor: tooltipBg,
      left: '-12px',
      top: '50%',
      transform: 'translateY(-50%)',
    },
  };
});

const Tooltip = ({
  children,
  title,
  placement = 'top',
  delay = 300,
  animation = 'fade',
  arrow = true,
  interactive = false,
  ...props
}) => {
  const [open, setOpen] = useState(false);

  const TransitionComponent = animation === 'zoom' ? Zoom : Fade;

  const handleOpen = () => {
    setTimeout(() => setOpen(true), delay);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <StyledTooltip
      title={title}
      placement={placement}
      arrow={arrow}
      open={open}
      onOpen={handleOpen}
      onClose={handleClose}
      interactive={interactive || undefined}
      TransitionComponent={TransitionComponent}
      TransitionProps={{ timeout: 200 }}
      enterDelay={delay}
      leaveDelay={100}
      {...props}
    >
      <span
        onMouseEnter={handleOpen}
        onMouseLeave={handleClose}
        onFocus={handleOpen}
        onBlur={handleClose}
        style={{ display: 'inline-block' }}
      >
        {children}
      </span>
    </StyledTooltip>
  );
};

export default Tooltip;