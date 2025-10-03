import { createTheme } from '@mui/material/styles';

// Design system values
const designSystem = {
  // Typography scale (1.25 ratio)
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.9375rem',  // 15px
    base: '1.125rem', // 18px
    lg: '1.5rem',     // 24px
    xl: '1.875rem',   // 30px
    '2xl': '2.3125rem', // 37px
    '3xl': '2.875rem',  // 46px
  },
  
  // Font weights
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  // Spacing system (4px base)
  spacing: {
    0: 0,
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
  },
  
  // Border radius
  borderRadius: {
    none: 0,
    sm: '0.125rem',   // 2px
    base: '0.25rem',  // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    full: '9999px',
  },
};

// Cyberpunk color palette with neon colors
const cyberpunkPalette = {
  primary: {
    50: '#e6ffff',
    100: '#b3ffff',
    200: '#80ffff',
    300: '#4dffff',
    400: '#1affff',
    500: '#00faff',  // Neon Cyan
    600: '#00c7cc',
    700: '#009499',
    800: '#006166',
    900: '#002e33',
    main: '#00faff',
    dark: '#00c7cc',
    light: '#1affff',
    contrastText: '#000000',
  },
  secondary: {
    50: '#ffe6ff',
    100: '#ffb3ff',
    200: '#ff80ff',
    300: '#ff4dff',
    400: '#ff1aff',
    500: '#ff00ff',  // Neon Magenta
    600: '#cc00cc',
    700: '#990099',
    800: '#660066',
    900: '#330033',
    main: '#ff00ff',
    dark: '#cc00cc',
    light: '#ff1aff',
    contrastText: '#000000',
  },
  success: {
    50: '#e6ffe6',
    100: '#b3ffb3',
    500: '#39ff14',  // Neon Green
    600: '#2ecc10',
    700: '#23990c',
    main: '#39ff14',
    dark: '#2ecc10',
    light: '#4dff17',
    contrastText: '#000000',
  },
  warning: {
    50: '#ffffe6',
    100: '#ffffb3',
    500: '#ffff00',  // Neon Yellow
    600: '#cccc00',
    700: '#999900',
    main: '#ffff00',
    dark: '#cccc00',
    light: '#ffff1a',
    contrastText: '#000000',
  },
  error: {
    50: '#ffe6ee',
    100: '#ffb3cc',
    500: '#ff0033',  // Neon Red
    600: '#cc0029',
    700: '#99001f',
    main: '#ff0033',
    dark: '#cc0029',
    light: '#ff1a4d',
    contrastText: '#ffffff',
  },
  info: {
    50: '#e6faff',
    100: '#b3e6ff',
    500: '#00bfff',  // Neon Blue
    600: '#0099cc',
    700: '#007399',
    main: '#00bfff',
    dark: '#0099cc',
    light: '#1ac6ff',
    contrastText: '#000000',
  },
  grey: {
    50: '#f0f0f0',
    100: '#d9d9d9',
    200: '#bfbfbf',
    300: '#a6a6a6',
    400: '#8c8c8c',
    500: '#737373',
    600: '#595959',
    700: '#404040',
    800: '#262626',
    900: '#0d0d0d',
  },
  background: {
    default: '#0d0d0d',     // Near black
    paper: '#1a1a1a',       // Dark grey
    secondary: '#000000',   // Pure black
    tertiary: '#000000',    // Pure black
  },
  text: {
    primary: '#ffffff',     // White
    secondary: '#00faff',   // Neon Cyan
    tertiary: '#ff00ff',    // Neon Magenta
    disabled: '#595959',    // Dark grey
  },
  divider: '#333333',       // Medium dark grey
};

// Create theme function with cyberpunk design
export const createAppTheme = (mode = 'dark') => {
  const palette = cyberpunkPalette;
  
  const isLight = mode === 'light';
  
  return createTheme({
    palette: {
      mode,
      ...palette,
      // Override colors based on mode
      background: {
        default: isLight ? '#f5f5f5' : '#0a0a0a',
        paper: isLight ? '#ffffff' : '#1a1a1a',
      },
      text: {
        primary: isLight ? '#333333' : '#ffffff',
        secondary: isLight ? '#666666' : '#cccccc',
      },
      divider: isLight ? '#e0e0e0' : '#333333',
    },
    typography: {
      fontFamily: "'Orbitron', sans-serif",
      fontWeightLight: designSystem.fontWeight.light,
      fontWeightRegular: designSystem.fontWeight.regular,
      fontWeightMedium: designSystem.fontWeight.medium,
      fontWeightBold: designSystem.fontWeight.bold,
      
      // Heading styles with proper hierarchy
      h1: {
        fontSize: designSystem.fontSize['3xl'],
        fontWeight: designSystem.fontWeight.bold,
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
        marginBottom: designSystem.spacing[6],
      },
      h2: {
        fontSize: designSystem.fontSize['2xl'],
        fontWeight: designSystem.fontWeight.bold,
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
        marginBottom: designSystem.spacing[5],
      },
      h3: {
        fontSize: designSystem.fontSize.xl,
        fontWeight: designSystem.fontWeight.semibold,
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
        marginBottom: designSystem.spacing[4],
      },
      h4: {
        fontSize: designSystem.fontSize.lg,
        fontWeight: designSystem.fontWeight.semibold,
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
        marginBottom: designSystem.spacing[3],
      },
      h5: {
        fontSize: designSystem.fontSize.base,
        fontWeight: designSystem.fontWeight.semibold,
        lineHeight: 1.4,
        letterSpacing: '0',
        marginBottom: designSystem.spacing[3],
      },
      h6: {
        fontSize: designSystem.fontSize.sm,
        fontWeight: designSystem.fontWeight.semibold,
        lineHeight: 1.4,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        marginBottom: designSystem.spacing[2],
      },
      
      // Body text styles
      body1: {
        fontSize: designSystem.fontSize.base,
        fontWeight: designSystem.fontWeight.regular,
        lineHeight: 1.5,
        letterSpacing: '0',
      },
      body2: {
        fontSize: designSystem.fontSize.sm,
        fontWeight: designSystem.fontWeight.regular,
        lineHeight: 1.4,
        letterSpacing: '0',
      },
      
      // UI element styles
      button: {
        fontSize: designSystem.fontSize.sm,
        fontWeight: designSystem.fontWeight.medium,
        lineHeight: 1.4,
        letterSpacing: '0.05em',
        textTransform: 'none',
      },
      caption: {
        fontSize: designSystem.fontSize.xs,
        fontWeight: designSystem.fontWeight.regular,
        lineHeight: 1.4,
        letterSpacing: '0.05em',
      },
      overline: {
        fontSize: designSystem.fontSize.xs,
        fontWeight: designSystem.fontWeight.medium,
        lineHeight: 1.4,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
      },
    },
    
    // Spacing system
    spacing: (factor) => `${0.25 * factor}rem`,
    
    // Shape system
    shape: {
      borderRadius: 8,
    },
    
    // Shadow system with cyberpunk glow effects (25 levels for MUI compatibility)
    shadows: [
      'none',
      '0 1px 3px rgba(0, 250, 255, 0.12), 0 1px 2px rgba(0, 250, 255, 0.24)',
      '0 3px 6px rgba(0, 250, 255, 0.16), 0 3px 6px rgba(0, 250, 255, 0.23)',
      '0 10px 20px rgba(0, 250, 255, 0.19), 0 6px 6px rgba(0, 250, 255, 0.23)',
      '0 14px 28px rgba(0, 250, 255, 0.25), 0 10px 10px rgba(0, 250, 255, 0.22)',
      '0 19px 38px rgba(0, 250, 255, 0.30), 0 15px 12px rgba(0, 250, 255, 0.22)',
      '0 24px 48px rgba(0, 250, 255, 0.35), 0 20px 15px rgba(0, 250, 255, 0.22)',
      '0 32px 64px rgba(0, 250, 255, 0.40), 0 25px 20px rgba(0, 250, 255, 0.22)',
      '0 40px 80px rgba(0, 250, 255, 0.45), 0 30px 25px rgba(0, 250, 255, 0.22)',
      '0 48px 96px rgba(0, 250, 255, 0.50), 0 35px 30px rgba(0, 250, 255, 0.22)',
      '0 56px 112px rgba(0, 250, 255, 0.55), 0 40px 35px rgba(0, 250, 255, 0.22)',
      '0 64px 128px rgba(0, 250, 255, 0.60), 0 45px 40px rgba(0, 250, 255, 0.22)',
      '0 72px 144px rgba(0, 250, 255, 0.65), 0 50px 45px rgba(0, 250, 255, 0.22)',
      '0 80px 160px rgba(0, 250, 255, 0.70), 0 55px 50px rgba(0, 250, 255, 0.22)',
      '0 88px 176px rgba(0, 250, 255, 0.75), 0 60px 55px rgba(0, 250, 255, 0.22)',
      '0 96px 192px rgba(0, 250, 255, 0.80), 0 65px 60px rgba(0, 250, 255, 0.22)',
      '0 104px 208px rgba(0, 250, 255, 0.85), 0 70px 65px rgba(0, 250, 255, 0.22)',
      '0 112px 224px rgba(0, 250, 255, 0.90), 0 75px 70px rgba(0, 250, 255, 0.22)',
      '0 120px 240px rgba(0, 250, 255, 0.95), 0 80px 75px rgba(0, 250, 255, 0.22)',
      '0 128px 256px rgba(0, 250, 255, 1.00), 0 85px 80px rgba(0, 250, 255, 0.22)',
      '0 136px 272px rgba(0, 250, 255, 1.00), 0 90px 85px rgba(0, 250, 255, 0.22)',
      '0 144px 288px rgba(0, 250, 255, 1.00), 0 95px 90px rgba(0, 250, 255, 0.22)',
      '0 152px 304px rgba(0, 250, 255, 1.00), 0 100px 95px rgba(0, 250, 255, 0.22)',
      '0 160px 320px rgba(0, 250, 255, 1.00), 0 105px 100px rgba(0, 250, 255, 0.22)',
      '0 168px 336px rgba(0, 250, 255, 1.00), 0 110px 105px rgba(0, 250, 255, 0.22)',
    ],
    
    // Component overrides
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: designSystem.borderRadius.md,
            textTransform: 'none',
            fontWeight: designSystem.fontWeight.medium,
            transition: 'all 0.3s ease',
            '&:hover': {
              boxShadow: '0 0 20px rgba(0, 250, 255, 0.5)',
              transform: 'translateY(-2px)',
            },
          },
          contained: {
            background: 'linear-gradient(45deg, #00faff 30%, #ff00ff 90%)',
            border: '1px solid #00faff',
            '&:hover': {
              background: 'linear-gradient(45deg, #ff00ff 30%, #00faff 90%)',
            },
          },
          outlined: {
            border: '2px solid #00faff',
            color: '#00faff',
            '&:hover': {
              border: '2px solid #ff00ff',
              color: '#ff00ff',
              backgroundColor: 'rgba(255, 0, 255, 0.1)',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: isLight ? '#ffffff' : '#1a1a1a',
            border: isLight ? '1px solid #e0e0e0' : '1px solid #333333',
            borderRadius: designSystem.borderRadius.lg,
            '&:hover': {
              border: '1px solid #00faff',
              boxShadow: '0 0 15px rgba(0, 250, 255, 0.3)',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: isLight ? '#e0e0e0' : '#333333',
              },
              '&:hover fieldset': {
                borderColor: '#00faff',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#ff00ff',
                boxShadow: '0 0 10px rgba(255, 0, 255, 0.3)',
              },
            },
          },
        },
      },
    },
  });
};

// Export default dark theme
const theme = createAppTheme('dark');
export default theme;