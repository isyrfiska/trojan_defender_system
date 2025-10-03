import React from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Breadcrumbs as MuiBreadcrumbs,
  Link,
  Typography,
  Box,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Home as HomeIcon,
  NavigateNext as NavigateNextIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Discord-inspired styled components
const StyledBreadcrumbs = styled(MuiBreadcrumbs)(({ theme }) => ({
  padding: theme.spacing(1, 0),
  '& .MuiBreadcrumbs-separator': {
    color: theme.palette.text.disabled,
    margin: theme.spacing(0, 1),
  },
}));

const BreadcrumbLink = styled(Link)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
  color: theme.palette.text.secondary,
  textDecoration: 'none',
  fontSize: theme.typography.body2.fontSize,
  fontWeight: theme.typography.fontWeightMedium,
  padding: theme.spacing(0.5, 1),
  borderRadius: theme.shape.borderRadius,
  transition: 'all 0.2s ease',
  cursor: 'pointer',
  '&:hover': {
    color: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
    transform: 'translateY(-1px)',
  },
  '&:focus': {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: '2px',
  },
}));

const CurrentPage = styled(Typography)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
  color: theme.palette.text.primary,
  fontSize: theme.typography.body2.fontSize,
  fontWeight: theme.typography.fontWeightSemiBold,
  padding: theme.spacing(0.5, 1),
}));

const BackButton = styled(IconButton)(({ theme }) => ({
  marginRight: theme.spacing(1),
  color: theme.palette.text.secondary,
  transition: 'all 0.2s ease',
  '&:hover': {
    color: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
    transform: 'translateX(-2px)',
  },
}));

const BreadcrumbContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(1, 0),
  borderBottom: `1px solid ${theme.palette.divider}`,
  marginBottom: theme.spacing(2),
}));

const routeLabels = {
  '/': 'Home',
  '/dashboard': 'Dashboard',
  '/scan': 'Scan Files',
  '/network-scan': 'Network Scan',
  '/scan-history': 'Scan History',
  '/scan-result': 'Scan Result',
  '/threatmap': 'Threat Map',
  '/threat-map': 'Threat Map',
  '/profile': 'Profile',
  '/settings': 'Settings',
  '/security-chat': 'Security Chat',
  '/help': 'Help & Support',
  '/login': 'Login',
  '/register': 'Register',
};

const Breadcrumbs = ({ maxItems = 4, showHome = true, showBackButton = true }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Don't show breadcrumbs on login/register pages
  if (['/login', '/register'].includes(location.pathname)) {
    return null;
  }

  const handleBack = () => {
    navigate(-1);
  };

  const breadcrumbItems = [];

  // Add home breadcrumb
  if (showHome) {
    breadcrumbItems.push({
      label: 'Home',
      path: '/dashboard',
      icon: <HomeIcon sx={{ fontSize: 16 }} />,
    });
  }

  // Build breadcrumb items from pathname
  let currentPath = '';
  pathnames.forEach((pathname, index) => {
    currentPath += `/${pathname}`;
    const isLast = index === pathnames.length - 1;
    
    // Get label from routeLabels or format pathname
    let label = routeLabels[currentPath] || pathname.replace(/-/g, ' ');
    
    // Capitalize first letter of each word
    label = label.replace(/\b\w/g, (l) => l.toUpperCase());
    
    // Handle dynamic routes (like /scan-result/:id)
    if (currentPath.includes('/scan-result/') && !isNaN(pathname)) {
      label = `Result #${pathname}`;
    }

    breadcrumbItems.push({
      label,
      path: currentPath,
      isLast,
    });
  });

  // Limit breadcrumb items if maxItems is set
  const displayItems = breadcrumbItems.length > maxItems 
    ? [
        breadcrumbItems[0], // Always show first item (Home)
        { label: '...', isEllipsis: true },
        ...breadcrumbItems.slice(-maxItems + 2) // Show last items
      ]
    : breadcrumbItems;

  return (
    <BreadcrumbContainer>
      {showBackButton && (
        <BackButton
          onClick={handleBack}
          size="small"
          aria-label="Go back"
        >
          <ArrowBackIcon fontSize="small" />
        </BackButton>
      )}
      
      <StyledBreadcrumbs
        maxItems={maxItems}
        separator={<NavigateNextIcon fontSize="small" />}
        aria-label="breadcrumb navigation"
      >
        {displayItems.map((item, index) => {
          if (item.isEllipsis) {
            return (
              <Typography
                key="ellipsis"
                color="text.secondary"
                sx={{ display: 'flex', alignItems: 'center' }}
              >
                ...
              </Typography>
            );
          }

          if (item.isLast) {
            return (
              <CurrentPage key={item.path} component="span">
                {item.icon}
                {item.label}
              </CurrentPage>
            );
          }

          return (
            <BreadcrumbLink
              key={item.path}
              component={RouterLink}
              to={item.path}
              underline="none"
            >
              {item.icon}
              {item.label}
            </BreadcrumbLink>
          );
        })}
      </StyledBreadcrumbs>
     </BreadcrumbContainer>
   );
 };
 
 export default Breadcrumbs;