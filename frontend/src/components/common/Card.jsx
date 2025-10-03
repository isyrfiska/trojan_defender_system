import React from 'react';
import { Card as MuiCard, CardContent, CardHeader, CardActions } from '@mui/material';
import { styled } from '@mui/material/styles';

// Custom styled card that integrates with our design system
const StyledCard = styled(MuiCard)(({ theme, variant, elevation }) => ({
  // Base styles from design system
  borderRadius: 'var(--radius-lg)',
  border: '1px solid var(--color-border)',
  backgroundColor: 'var(--color-surface)',
  transition: 'all 0.2s ease-in-out',
  
  // Elevation variants
  ...(elevation === 'none' && {
    boxShadow: 'none',
  }),
  ...(elevation === 'sm' && {
    boxShadow: 'var(--shadow-sm)',
  }),
  ...(elevation === 'md' && {
    boxShadow: 'var(--shadow-md)',
  }),
  ...(elevation === 'lg' && {
    boxShadow: 'var(--shadow-lg)',
  }),
  
  // Variant styles
  ...(variant === 'outlined' && {
    backgroundColor: 'transparent',
    border: '2px solid var(--color-border)',
  }),
  ...(variant === 'filled' && {
    backgroundColor: 'var(--color-surface-variant)',
    border: 'none',
  }),
  
  // Hover effects
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: 'var(--shadow-lg)',
  },
  
  // Focus within for accessibility
  '&:focus-within': {
    outline: '2px solid var(--color-primary-500)',
    outlineOffset: '2px',
  },
}));

const StyledCardHeader = styled(CardHeader)(({ theme }) => ({
  padding: 'var(--space-6)',
  borderBottom: '1px solid var(--color-border)',
  
  '& .MuiCardHeader-title': {
    fontSize: 'var(--font-size-lg)',
    fontWeight: 'var(--font-weight-semibold)',
    lineHeight: 'var(--line-height-tight)',
    color: 'var(--color-text-primary)',
  },
  
  '& .MuiCardHeader-subheader': {
    fontSize: 'var(--font-size-sm)',
    fontWeight: 'var(--font-weight-normal)',
    lineHeight: 'var(--line-height-normal)',
    color: 'var(--color-text-secondary)',
    marginTop: 'var(--space-1)',
  },
}));

const StyledCardContent = styled(CardContent)(({ theme, padding }) => ({
  padding: padding === 'none' ? 0 : 'var(--space-6)',
  
  '&:last-child': {
    paddingBottom: padding === 'none' ? 0 : 'var(--space-6)',
  },
  
  // Typography within card content
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    color: 'var(--color-text-primary)',
    marginBottom: 'var(--space-3)',
  },
  
  '& p': {
    color: 'var(--color-text-secondary)',
    lineHeight: 'var(--line-height-normal)',
    marginBottom: 'var(--space-4)',
    
    '&:last-child': {
      marginBottom: 0,
    },
  },
}));

const StyledCardActions = styled(CardActions)(({ theme, justify }) => ({
  padding: 'var(--space-4) var(--space-6)',
  borderTop: '1px solid var(--color-border)',
  gap: 'var(--space-2)',
  
  ...(justify === 'center' && {
    justifyContent: 'center',
  }),
  ...(justify === 'end' && {
    justifyContent: 'flex-end',
  }),
  ...(justify === 'between' && {
    justifyContent: 'space-between',
  }),
}));

const Card = ({
  children,
  variant = 'elevation',
  elevation = 'sm',
  className = '',
  ...props
}) => {
  return (
    <StyledCard
      variant={variant}
      elevation={elevation}
      className={`card ${className}`}
      {...props}
    >
      {children}
    </StyledCard>
  );
};

// Card sub-components
Card.Header = ({ title, subheader, action, avatar, className = '', ...props }) => (
  <StyledCardHeader
    title={title}
    subheader={subheader}
    action={action}
    avatar={avatar}
    className={`card-header ${className}`}
    {...props}
  />
);
Card.Header.displayName = 'CardHeader';

Card.Content = ({ children, padding = 'normal', className = '', ...props }) => (
  <StyledCardContent
    padding={padding}
    className={`card-content ${className}`}
    {...props}
  >
    {children}
  </StyledCardContent>
);
Card.Content.displayName = 'CardContent';

Card.Actions = ({ children, justify = 'start', className = '', ...props }) => (
  <StyledCardActions
    justify={justify}
    className={`card-actions ${className}`}
    {...props}
  >
    {children}
  </StyledCardActions>
);
Card.Actions.displayName = 'CardActions';

// Predefined card variants for common use cases
export const InfoCard = ({ title, children, ...props }) => (
  <Card variant="outlined" {...props}>
    {title && <Card.Header title={title} />}
    <Card.Content>{children}</Card.Content>
  </Card>
);

export const StatCard = ({ title, value, subtitle, icon, ...props }) => (
  <Card elevation="md" {...props}>
    <Card.Content>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)' }}>
            {value}
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: 'var(--font-size-sm)' }}>
            {title}
          </p>
          {subtitle && (
            <p style={{ margin: '2px 0 0 0', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
              {subtitle}
            </p>
          )}
        </div>
        {icon && (
          <div style={{ color: 'var(--color-primary-500)', fontSize: '2rem' }}>
            {icon}
          </div>
        )}
      </div>
    </Card.Content>
  </Card>
);

export default Card;