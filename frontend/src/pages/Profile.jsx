import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Avatar,
  Divider,
  CircularProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
  InputAdornment,
  Tabs,
  Tab,
  Alert,
} from '@mui/material';
import {
  Person,
  Email,
  Phone,
  Security,
  Notifications,
  Edit,
  Save,
  Cancel,
  Visibility,
  VisibilityOff,
  History,
  Delete,
  CloudUpload,
  Warning,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useAlert } from '../hooks/useAlert';

const Profile = () => {
  const { user, updateProfile, updatePassword } = useAuth();
  const { addAlert } = useAlert();
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [deleteAccountDialogOpen, setDeleteAccountDialogOpen] = useState(false);
  const [profileData, setProfileData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    company: '',
    jobTitle: '',
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordErrors, setPasswordErrors] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [notificationSettings, setNotificationSettings] = useState({
    emailAlerts: true,
    securityUpdates: true,
    threatAlerts: true,
    marketingEmails: false,
  });

  useEffect(() => {
    if (user) {
      // In a real app, we might fetch additional profile data from an API
      setProfileData({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        email: user.email || '',
        phone: user.phone || '',
        company: user.company || '',
        jobTitle: user.jobTitle || '',
      });
      setLoading(false);
    }
  }, [user]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleEditToggle = () => {
    if (editMode) {
      // Cancel edit mode
      setProfileData({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        email: user.email || '',
        phone: user.phone || '',
        company: user.company || '',
        jobTitle: user.jobTitle || '',
      });
    }
    setEditMode(!editMode);
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData({
      ...profileData,
      [name]: value,
    });
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData({
      ...passwordData,
      [name]: value,
    });

    // Clear errors when typing
    if (passwordErrors[name]) {
      setPasswordErrors({
        ...passwordErrors,
        [name]: '',
      });
    }
  };

  const handleNotificationChange = (e) => {
    const { name, checked } = e.target;
    setNotificationSettings({
      ...notificationSettings,
      [name]: checked,
    });
  };

  const validatePasswordForm = () => {
    const errors = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    };
    let isValid = true;

    if (!passwordData.currentPassword) {
      errors.currentPassword = 'Current password is required';
      isValid = false;
    }

    if (!passwordData.newPassword) {
      errors.newPassword = 'New password is required';
      isValid = false;
    } else if (passwordData.newPassword.length < 8) {
      errors.newPassword = 'Password must be at least 8 characters';
      isValid = false;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
      isValid = false;
    }

    setPasswordErrors(errors);
    return isValid;
  };

  const handleSaveProfile = async () => {
    try {
      // In a real app, this would call the API to update the profile
      await updateProfile(profileData);
      setEditMode(false);
      addAlert({
        message: 'Profile updated successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      addAlert({
        message: 'Failed to update profile. Please try again.',
        severity: 'error',
      });
    }
  };

  const handleUpdatePassword = async () => {
    if (!validatePasswordForm()) return;

    try {
      // In a real app, this would call the API to update the password
      await updatePassword(
        passwordData.currentPassword,
        passwordData.newPassword
      );
      
      // Reset form
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      
      addAlert({
        message: 'Password updated successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error updating password:', error);
      addAlert({
        message: 'Failed to update password. Please check your current password.',
        severity: 'error',
      });
    }
  };

  const handleSaveNotifications = () => {
    // In a real app, this would call the API to update notification settings
    addAlert({
      message: 'Notification settings updated successfully',
      severity: 'success',
    });
  };

  const handleDeleteAccount = () => {
    // In a real app, this would call the API to delete the account
    setDeleteAccountDialogOpen(false);
    addAlert({
      message: 'Account deletion request submitted. You will receive a confirmation email.',
      severity: 'info',
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          My Profile
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and manage your account information
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Left column - Profile summary */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  mx: 'auto',
                  mb: 2,
                  bgcolor: 'primary.main',
                  fontSize: 40,
                }}
              >
                {profileData.firstName && profileData.lastName
                  ? `${profileData.firstName[0]}${profileData.lastName[0]}`
                  : <Person fontSize="large" />}
              </Avatar>
              
              <Typography variant="h5" gutterBottom>
                {profileData.firstName} {profileData.lastName}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {profileData.email}
              </Typography>
              
              {profileData.jobTitle && profileData.company && (
                <Typography variant="body2" color="text.secondary">
                  {profileData.jobTitle} at {profileData.company}
                </Typography>
              )}

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  size="small"
                >
                  Change Photo
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Person fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Account Type"
                    secondary="Standard User"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <History fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Member Since"
                    secondary="June 2023"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Security fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Last Password Change"
                    secondary="30 days ago"
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Button
                variant="outlined"
                color="error"
                startIcon={<Delete />}
                fullWidth
                onClick={() => setDeleteAccountDialogOpen(true)}
              >
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Right column - Tabs for different settings */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ borderRadius: 2 }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              <Tab label="Personal Information" />
              <Tab label="Security" />
              <Tab label="Notifications" />
            </Tabs>

            <Box sx={{ p: 3 }}>
              {/* Personal Information Tab */}
              {tabValue === 0 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                    <Typography variant="h6">
                      Personal Information
                    </Typography>
                    <Button
                      startIcon={editMode ? <Cancel /> : <Edit />}
                      onClick={handleEditToggle}
                      color={editMode ? 'error' : 'primary'}
                    >
                      {editMode ? 'Cancel' : 'Edit'}
                    </Button>
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="First Name"
                        name="firstName"
                        value={profileData.firstName}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Last Name"
                        name="lastName"
                        value={profileData.lastName}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Email Address"
                        name="email"
                        type="email"
                        value={profileData.email}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Email />
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Phone Number"
                        name="phone"
                        value={profileData.phone}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Phone />
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Company"
                        name="company"
                        value={profileData.company}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Job Title"
                        name="jobTitle"
                        value={profileData.jobTitle}
                        onChange={handleProfileChange}
                        disabled={!editMode}
                        margin="normal"
                      />
                    </Grid>
                  </Grid>

                  {editMode && (
                    <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<Save />}
                        onClick={handleSaveProfile}
                      >
                        Save Changes
                      </Button>
                    </Box>
                  )}
                </Box>
              )}

              {/* Security Tab */}
              {tabValue === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Change Password
                  </Typography>

                  <Alert severity="info" sx={{ mb: 3 }}>
                    Strong passwords include a mix of letters, numbers, and symbols. Avoid using personal information.
                  </Alert>

                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Current Password"
                        name="currentPassword"
                        type={showPassword ? 'text' : 'password'}
                        value={passwordData.currentPassword}
                        onChange={handlePasswordChange}
                        margin="normal"
                        error={!!passwordErrors.currentPassword}
                        helperText={passwordErrors.currentPassword}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowPassword(!showPassword)}
                                edge="end"
                              >
                                {showPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="New Password"
                        name="newPassword"
                        type={showNewPassword ? 'text' : 'password'}
                        value={passwordData.newPassword}
                        onChange={handlePasswordChange}
                        margin="normal"
                        error={!!passwordErrors.newPassword}
                        helperText={passwordErrors.newPassword}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowNewPassword(!showNewPassword)}
                                edge="end"
                              >
                                {showNewPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Confirm New Password"
                        name="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={passwordData.confirmPassword}
                        onChange={handlePasswordChange}
                        margin="normal"
                        error={!!passwordErrors.confirmPassword}
                        helperText={passwordErrors.confirmPassword}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                edge="end"
                              >
                                {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleUpdatePassword}
                    >
                      Update Password
                    </Button>
                  </Box>

                  <Divider sx={{ my: 4 }} />

                  <Typography variant="h6" gutterBottom>
                    Two-Factor Authentication
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Add an extra layer of security to your account by enabling two-factor authentication.
                  </Typography>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<Security />}
                  >
                    Enable Two-Factor Authentication
                  </Button>
                </Box>
              )}

              {/* Notifications Tab */}
              {tabValue === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Notification Settings
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Manage how you receive notifications and alerts from our system.
                  </Typography>

                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <Notifications />
                      </ListItemIcon>
                      <ListItemText
                        primary="Email Alerts"
                        secondary="Receive important alerts via email"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={notificationSettings.emailAlerts}
                            onChange={handleNotificationChange}
                            name="emailAlerts"
                            color="primary"
                          />
                        }
                        label=""
                      />
                    </ListItem>
                    <Divider variant="inset" component="li" />
                    <ListItem>
                      <ListItemIcon>
                        <Security />
                      </ListItemIcon>
                      <ListItemText
                        primary="Security Updates"
                        secondary="Get notified about security patches and updates"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={notificationSettings.securityUpdates}
                            onChange={handleNotificationChange}
                            name="securityUpdates"
                            color="primary"
                          />
                        }
                        label=""
                      />
                    </ListItem>
                    <Divider variant="inset" component="li" />
                    <ListItem>
                      <ListItemIcon>
                        <Warning />
                      </ListItemIcon>
                      <ListItemText
                        primary="Threat Alerts"
                        secondary="Receive alerts about new threats and vulnerabilities"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={notificationSettings.threatAlerts}
                            onChange={handleNotificationChange}
                            name="threatAlerts"
                            color="primary"
                          />
                        }
                        label=""
                      />
                    </ListItem>
                    <Divider variant="inset" component="li" />
                    <ListItem>
                      <ListItemIcon>
                        <Email />
                      </ListItemIcon>
                      <ListItemText
                        primary="Marketing Emails"
                        secondary="Receive promotional emails and newsletters"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={notificationSettings.marketingEmails}
                            onChange={handleNotificationChange}
                            name="marketingEmails"
                            color="primary"
                          />
                        }
                        label=""
                      />
                    </ListItem>
                  </List>

                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleSaveNotifications}
                    >
                      Save Preferences
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Delete Account Dialog */}
      <Dialog
        open={deleteAccountDialogOpen}
        onClose={() => setDeleteAccountDialogOpen(false)}
      >
        <DialogTitle>Delete Your Account?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This action cannot be undone. All your data, including scan history and settings, will be permanently deleted.
          </DialogContentText>
          <DialogContentText sx={{ mt: 2, fontWeight: 'bold', color: 'error.main' }}>
            Are you sure you want to delete your account?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAccountDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteAccount} color="error">
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Profile;