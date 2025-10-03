import React, { useState } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  FormControl,
  FormLabel,
  FormHelperText,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { Visibility, VisibilityOff } from '@mui/icons-material';

// Custom styled text field that integrates with our design system
const StyledTextField = styled(TextField)(({ theme, size, variant }) => ({
  // Base styles from design system
  '& .MuiInputBase-root': {
    fontFamily: 'var(--font-family-primary)',
    fontSize: 'var(--font-size-base)',
    lineHeight: 'var(--line-height-ui)',
    borderRadius: 'var(--radius-md)',
    transition: 'all 0.2s ease-in-out',
    backgroundColor: 'var(--color-surface)',
    
    // Size variants
    ...(size === 'small' && {
      height: '2rem', // 32px
      fontSize: 'var(--font-size-sm)',
    }),
    ...(size === 'medium' && {
      height: '2.5rem', // 40px
      fontSize: 'var(--font-size-base)',
    }),
    ...(size === 'large' && {
      height: '3rem', // 48px
      fontSize: 'var(--font-size-lg)',
    }),
    
    '&:hover': {
      backgroundColor: 'var(--color-surface-hover)',
    },
    
    '&.Mui-focused': {
      backgroundColor: 'var(--color-surface)',
      boxShadow: '0 0 0 2px var(--color-primary-500)',
    },
    
    '&.Mui-error': {
      borderColor: 'var(--color-error-500)',
      
      '&.Mui-focused': {
        boxShadow: '0 0 0 2px var(--color-error-500)',
      },
    },
  },
  
  // Input text styling
  '& .MuiInputBase-input': {
    padding: '0 var(--space-3)',
    color: 'var(--color-text-primary)',
    
    '&::placeholder': {
      color: 'var(--color-text-tertiary)',
      opacity: 1,
    },
  },
  
  // Label styling
  '& .MuiInputLabel-root': {
    fontSize: 'var(--font-size-sm)',
    fontWeight: 'var(--font-weight-medium)',
    color: 'var(--color-text-secondary)',
    
    '&.Mui-focused': {
      color: 'var(--color-primary-500)',
    },
    
    '&.Mui-error': {
      color: 'var(--color-error-500)',
    },
  },
  
  // Helper text styling
  '& .MuiFormHelperText-root': {
    fontSize: 'var(--font-size-xs)',
    marginTop: 'var(--space-1)',
    marginLeft: 0,
    
    '&.Mui-error': {
      color: 'var(--color-error-500)',
    },
  },
  
  // Outlined variant
  '& .MuiOutlinedInput-root': {
    '& fieldset': {
      borderColor: 'var(--color-border)',
      borderWidth: '1px',
    },
    
    '&:hover fieldset': {
      borderColor: 'var(--color-border-hover)',
    },
    
    '&.Mui-focused fieldset': {
      borderColor: 'var(--color-primary-500)',
      borderWidth: '2px',
    },
    
    '&.Mui-error fieldset': {
      borderColor: 'var(--color-error-500)',
    },
  },
  
  // Filled variant
  '& .MuiFilledInput-root': {
    backgroundColor: 'var(--color-surface-variant)',
    
    '&:hover': {
      backgroundColor: 'var(--color-surface-variant-hover)',
    },
    
    '&.Mui-focused': {
      backgroundColor: 'var(--color-surface-variant)',
    },
  },
}));

const Input = ({
  label,
  type = 'text',
  size = 'medium',
  variant = 'outlined',
  error = false,
  helperText,
  required = false,
  disabled = false,
  fullWidth = true,
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  startIcon,
  endIcon,
  multiline = false,
  rows = 4,
  className = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);
  
  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };
  
  const inputType = type === 'password' && showPassword ? 'text' : type;
  
  const startAdornment = startIcon ? (
    <InputAdornment position="start">
      {startIcon}
    </InputAdornment>
  ) : null;
  
  const endAdornment = (
    <InputAdornment position="end">
      {type === 'password' && (
        <IconButton
          onClick={handleTogglePassword}
          edge="end"
          size="small"
          aria-label="toggle password visibility"
        >
          {showPassword ? <VisibilityOff /> : <Visibility />}
        </IconButton>
      )}
      {endIcon && type !== 'password' && endIcon}
    </InputAdornment>
  );
  
  return (
    <StyledTextField
      label={label}
      type={inputType}
      size={size}
      variant={variant}
      error={error}
      helperText={helperText}
      required={required}
      disabled={disabled}
      fullWidth={fullWidth}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      onFocus={onFocus}
      multiline={multiline}
      rows={multiline ? rows : undefined}
      className={`input ${className}`}
      InputProps={{
        startAdornment,
        endAdornment: (startIcon || endIcon || type === 'password') ? endAdornment : null,
      }}
      {...props}
    />
  );
};

// Predefined input variants for common use cases
export const EmailInput = (props) => (
  <Input
    type="email"
    label="Email Address"
    placeholder="Enter your email"
    {...props}
  />
);

export const PasswordInput = (props) => (
  <Input
    type="password"
    label="Password"
    placeholder="Enter your password"
    {...props}
  />
);

export const SearchInput = ({ onSearch, ...props }) => (
  <Input
    type="search"
    placeholder="Search..."
    {...props}
  />
);

export const TextArea = (props) => (
  <Input
    multiline
    rows={4}
    {...props}
  />
);

export default Input;