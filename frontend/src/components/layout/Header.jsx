import { useState, useContext } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  MenuItem,
  Avatar,
  Tooltip,
  Divider,
  Badge,
  ListItemIcon,
  ListItemText,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Settings,
  Security,
  Person as PersonIcon,
  ExitToApp as ExitToAppIcon,
} from '@mui/icons-material';
import { useTheme } from '../../hooks/useTheme';
import useWebSocket from '../../hooks/useWebSocket';
import { GlitchText } from '../effects';
import ConfirmDialog from '../common/ConfirmDialog';

const Header = ({ toggleSidebar }) => {
  const { colorMode, toggleColorMode } = useTheme();
  const { threatEvents } = useWebSocket();
  const navigate = useNavigate();
  const { isAuthenticated, currentUser, logout } = useContext(AuthContext);
  
  const [anchorElUser, setAnchorElUser] = useState(null);
  const [anchorElNotifications, setAnchorElNotifications] = useState(null);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const handleOpenNotificationsMenu = (event) => {
    setAnchorElNotifications(event.currentTarget);
  };

  const handleCloseNotificationsMenu = () => {
    setAnchorElNotifications(null);
  };

  const handleProfileClick = () => {
    handleCloseUserMenu();
    navigate('/profile');
  };

  const handleSettingsClick = () => {
    handleCloseUserMenu();
    navigate('/settings');
  };
  
  const handleLogoutClick = () => {
    handleCloseUserMenu();
    setLogoutDialogOpen(true);
  };
  
  const handleLogoutCancel = () => {
    setLogoutDialogOpen(false);
  };
  
  const handleLogoutConfirm = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
      setLogoutDialogOpen(false);
    }
  };

  return (
    <AppBar position="fixed" color="primary" elevation={0}>
      <Toolbar>
        {isAuthenticated && (
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleSidebar}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}

        <GlitchText
          variant="h6"
          component={RouterLink}
          to="/"
          intensity="low"
          trigger="hover"
          sx={{
            mr: 2,
            fontWeight: 700,
            color: 'inherit',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Security sx={{ mr: 1 }} />
          Trojan Defender
        </GlitchText>

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title={`Switch to ${colorMode === 'dark' ? 'light' : 'dark'} mode`}>
          <IconButton 
            onClick={toggleColorMode} 
            color="inherit"
            sx={{
              mr: 1,
              transition: 'all 0.3s ease',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                transform: 'scale(1.1)',
              }
            }}
          >
            {colorMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Tooltip>

        {isAuthenticated && currentUser ? (
          <>
            <Tooltip title="Notifications">
              <IconButton 
                color="inherit"
                onClick={handleOpenNotificationsMenu}
                sx={{
                  mr: 1,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    transform: 'scale(1.1)',
                  }
                }}
              >
                <Badge badgeContent={threatEvents?.length || 0} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>

            <Menu
              anchorEl={anchorElNotifications}
              open={Boolean(anchorElNotifications)}
              onClose={handleCloseNotificationsMenu}
              PaperProps={{
                sx: {
                  maxWidth: 300,
                  maxHeight: 400,
                },
              }}
            >
              {threatEvents && threatEvents.length > 0 ? (
                threatEvents.slice(0, 5).map((event, index) => (
                  <MenuItem key={index} onClick={handleCloseNotificationsMenu}>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {event.type || 'Security Alert'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {event.message || event.description || 'New threat detected'}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))
              ) : (
                <MenuItem onClick={handleCloseNotificationsMenu}>
                  <Typography variant="body2" color="text.secondary">
                    No new notifications
                  </Typography>
                </MenuItem>
              )}
            </Menu>

            <Tooltip title="Account settings">
              <IconButton 
                onClick={handleOpenUserMenu} 
                sx={{ 
                  p: 0, 
                  ml: 2,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'scale(1.05)',
                  }
                }}
              >
                <Avatar
                  alt={currentUser?.username || currentUser?.email || 'User'}
                  src={currentUser?.avatar || ''}
                  sx={{ 
                    bgcolor: 'primary.main',
                    '&:hover': {
                      boxShadow: '0 0 8px rgba(0, 0, 0, 0.3)',
                    }
                  }}
                >
                  {(currentUser?.username || currentUser?.email || 'U').charAt(0).toUpperCase()}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu
              sx={{ mt: '45px' }}
              anchorEl={anchorElUser}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorElUser)}
              onClose={handleCloseUserMenu}
              PaperProps={{
                elevation: 3,
                sx: {
                  overflow: 'visible',
                  filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.2))',
                  minWidth: 200,
                },
              }}
            >
              <MenuItem onClick={handleProfileClick}>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>
                  <Typography variant="body2">Profile</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {currentUser?.email || currentUser?.username || 'View profile'}
                  </Typography>
                </ListItemText>
              </MenuItem>
              <MenuItem onClick={handleSettingsClick}>
                <ListItemIcon>
                  <Settings fontSize="small" />
                </ListItemIcon>
                <ListItemText>Settings</ListItemText>
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogoutClick}>
                <ListItemIcon>
                  <ExitToAppIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Logout</ListItemText>
              </MenuItem>
            </Menu>
          </>
        ) : (
          <Box sx={{ display: 'flex' }}>
            <Button
              component={RouterLink}
              to="/login"
              color="inherit"
              sx={{ 
                ml: 1,
                fontWeight: 600,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                }
              }}
            >
              Login
            </Button>
            <Button
              component={RouterLink}
              to="/register"
              color="inherit"
              variant="outlined"
              sx={{ 
                ml: 1,
                fontWeight: 600,
                borderWidth: 2,
                '&:hover': {
                  borderWidth: 2,
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                }
              }}
            >
              Register
            </Button>
          </Box>
        )}
      </Toolbar>
      
      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        open={logoutDialogOpen}
        title="Confirm Logout"
        message="Are you sure you want to logout? You will need to sign in again to access your account."
        confirmText="Logout"
        cancelText="Cancel"
        onConfirm={handleLogoutConfirm}
        onCancel={handleLogoutCancel}
        loading={isLoggingOut}
        severity="warning"
      />
    </AppBar>
  );
};

export default Header;