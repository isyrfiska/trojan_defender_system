import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, CssBaseline, useTheme } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import { Breadcrumbs, SessionTimeout } from '../common';
import { useAuth } from '../../hooks/useAuth';

const drawerWidth = 280;
const collapsedDrawerWidth = 80;

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isAuthenticated, currentUser } = useAuth();
  const theme = useTheme();
  
  // Determine if sidebar should be shown
  const showSidebar = isAuthenticated && currentUser;

  console.log('Layout: isAuthenticated =', isAuthenticated); // Debug log

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <SessionTimeout />
      <CssBaseline />
      <Header toggleSidebar={toggleSidebar} />
      
      <Box sx={{ display: 'flex', flex: 1 }}>
        {showSidebar && (
          <Sidebar open={sidebarOpen} toggleSidebar={toggleSidebar} />
        )}
        
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            width: {
              xs: '100%',
              sm: sidebarOpen ? `calc(100% - ${drawerWidth}px)` : `calc(100% - ${collapsedDrawerWidth}px)`
            },
            ml: {
              xs: 0,
              sm: sidebarOpen ? `${drawerWidth}px` : `${collapsedDrawerWidth}px`
            },
            minHeight: 'calc(100vh - 64px - 60px)', // Account for header (64px) and footer (60px)
            mb: '60px', // Account for fixed footer height
            p: { xs: 2, sm: 3 },
            transition: theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          }}
        >
          {showSidebar && <Breadcrumbs />}
          <Outlet />
        </Box>
      </Box>
      
      <Footer />
    </Box>
  );
};

export default Layout;