import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Card,
  CardContent,
  Alert,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  DarkMode,
  Notifications,
  Security,
  Language,
  Storage,
  Refresh,
  Save,
  Delete,
  CloudDownload,
  CloudUpload,
  Info,
  Warning,
  SettingsBackupRestore,
} from '@mui/icons-material';
import { useTheme } from '../hooks/useTheme';
import { useAlert } from '../hooks/useAlert';

const Settings = () => {
  const { theme, toggleTheme } = useTheme();
  const { addAlert } = useAlert();
  
  // Application settings
  const [appSettings, setAppSettings] = useState({
    language: 'en',
    autoScan: true,
    scanArchives: true,
    deepScan: false,
    useAI: true,
    autoUpdate: true,
    telemetry: true,
    cacheSize: 500, // MB
    maxLogSize: 200, // MB
    retentionPeriod: 30, // days
  });

  // Security settings
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorAuth: false,
    sessionTimeout: 30, // minutes
    passwordExpiry: 90, // days
    apiKeyEnabled: false,
    apiKey: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
  });

  // Notification settings
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    threatAlerts: true,
    scanCompletionAlerts: true,
    updateNotifications: true,
    marketingEmails: false,
  });

  const handleAppSettingChange = (event) => {
    const { name, value, checked } = event.target;
    setAppSettings({
      ...appSettings,
      [name]: event.target.type === 'checkbox' ? checked : value,
    });
  };

  const handleSecuritySettingChange = (event) => {
    const { name, value, checked } = event.target;
    setSecuritySettings({
      ...securitySettings,
      [name]: event.target.type === 'checkbox' ? checked : value,
    });
  };

  const handleNotificationSettingChange = (event) => {
    const { name, checked } = event.target;
    setNotificationSettings({
      ...notificationSettings,
      [name]: checked,
    });
  };

  const handleSliderChange = (name) => (event, newValue) => {
    setAppSettings({
      ...appSettings,
      [name]: newValue,
    });
  };

  const handleSaveSettings = () => {
    // In a real app, this would save settings to the backend
    addAlert({
      message: 'Settings saved successfully',
      severity: 'success',
    });
  };

  const handleResetSettings = () => {
    // Reset to default settings
    setAppSettings({
      language: 'en',
      autoScan: true,
      scanArchives: true,
      deepScan: false,
      useAI: true,
      autoUpdate: true,
      telemetry: true,
      cacheSize: 500,
      maxLogSize: 200,
      retentionPeriod: 30,
    });
    
    setSecuritySettings({
      twoFactorAuth: false,
      sessionTimeout: 30,
      passwordExpiry: 90,
      apiKeyEnabled: false,
      apiKey: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    });
    
    setNotificationSettings({
      emailNotifications: true,
      threatAlerts: true,
      scanCompletionAlerts: true,
      updateNotifications: true,
      marketingEmails: false,
    });
    
    addAlert({
      message: 'Settings reset to defaults',
      severity: 'info',
    });
  };

  const handleExportSettings = () => {
    // In a real app, this would export settings to a JSON file
    const settingsData = {
      app: appSettings,
      security: securitySettings,
      notifications: notificationSettings,
    };
    
    const dataStr = JSON.stringify(settingsData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'trojan-defender-settings.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    addAlert({
      message: 'Settings exported successfully',
      severity: 'success',
    });
  };

  const handleGenerateApiKey = () => {
    // In a real app, this would call the backend to generate a new API key
    const newApiKey = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'.replace(/[x]/g, () => {
      return Math.floor(Math.random() * 16).toString(16);
    });
    
    setSecuritySettings({
      ...securitySettings,
      apiKey: newApiKey,
    });
    
    addAlert({
      message: 'New API key generated',
      severity: 'success',
    });
  };

  const handleClearCache = () => {
    // In a real app, this would clear the application cache
    addAlert({
      message: 'Cache cleared successfully',
      severity: 'success',
    });
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure application preferences and security settings
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Left column - Quick settings */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Settings
              </Typography>
              
              <List>
                <ListItem>
                  <ListItemIcon>
                    <DarkMode />
                  </ListItemIcon>
                  <ListItemText
                    primary="Dark Mode"
                    secondary={theme === 'dark' ? 'Enabled' : 'Disabled'}
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={theme === 'dark'}
                        onChange={toggleTheme}
                        name="darkMode"
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
                    primary="Auto-Scan Files"
                    secondary="Automatically scan files when uploaded"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={appSettings.autoScan}
                        onChange={handleAppSettingChange}
                        name="autoScan"
                        color="primary"
                      />
                    }
                    label=""
                  />
                </ListItem>
                
                <Divider variant="inset" component="li" />
                
                <ListItem>
                  <ListItemIcon>
                    <Notifications />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Receive alerts via email"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={notificationSettings.emailNotifications}
                        onChange={handleNotificationSettingChange}
                        name="emailNotifications"
                        color="primary"
                      />
                    }
                    label=""
                  />
                </ListItem>
                
                <Divider variant="inset" component="li" />
                
                <ListItem>
                  <ListItemIcon>
                    <Refresh />
                  </ListItemIcon>
                  <ListItemText
                    primary="Auto Updates"
                    secondary="Keep application up to date"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={appSettings.autoUpdate}
                        onChange={handleAppSettingChange}
                        name="autoUpdate"
                        color="primary"
                      />
                    }
                    label=""
                  />
                </ListItem>
              </List>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  startIcon={<CloudDownload />}
                  onClick={handleExportSettings}
                  size="small"
                >
                  Export
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  size="small"
                >
                  Import
                </Button>
                
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<SettingsBackupRestore />}
                  onClick={handleResetSettings}
                  size="small"
                >
                  Reset
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Storage Management
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" gutterBottom>
                  Cache Size: {appSettings.cacheSize} MB
                </Typography>
                <Slider
                  value={appSettings.cacheSize}
                  onChange={handleSliderChange('cacheSize')}
                  aria-labelledby="cache-size-slider"
                  valueLabelDisplay="auto"
                  step={100}
                  marks
                  min={100}
                  max={1000}
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" gutterBottom>
                  Log Retention: {appSettings.retentionPeriod} days
                </Typography>
                <Slider
                  value={appSettings.retentionPeriod}
                  onChange={handleSliderChange('retentionPeriod')}
                  aria-labelledby="retention-slider"
                  valueLabelDisplay="auto"
                  step={15}
                  marks
                  min={15}
                  max={90}
                />
              </Box>
              
              <Button
                variant="outlined"
                startIcon={<Delete />}
                onClick={handleClearCache}
                fullWidth
              >
                Clear Cache
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Right column - Detailed settings */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ borderRadius: 2, p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Application Settings
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="language-select-label">Language</InputLabel>
                  <Select
                    labelId="language-select-label"
                    id="language-select"
                    value={appSettings.language}
                    label="Language"
                    name="language"
                    onChange={handleAppSettingChange}
                    startAdornment={<Language sx={{ mr: 1 }} />}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Español</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                    <MenuItem value="de">Deutsch</MenuItem>
                    <MenuItem value="zh">中文</MenuItem>
                    <MenuItem value="ja">日本語</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="session-timeout-label">Session Timeout</InputLabel>
                  <Select
                    labelId="session-timeout-label"
                    id="session-timeout"
                    value={securitySettings.sessionTimeout}
                    label="Session Timeout"
                    name="sessionTimeout"
                    onChange={handleSecuritySettingChange}
                  >
                    <MenuItem value={15}>15 minutes</MenuItem>
                    <MenuItem value={30}>30 minutes</MenuItem>
                    <MenuItem value={60}>1 hour</MenuItem>
                    <MenuItem value={120}>2 hours</MenuItem>
                    <MenuItem value={240}>4 hours</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Scanning Options
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={appSettings.scanArchives}
                          onChange={handleAppSettingChange}
                          name="scanArchives"
                          color="primary"
                        />
                      }
                      label="Scan Archive Files (zip, rar, etc.)"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={appSettings.deepScan}
                          onChange={handleAppSettingChange}
                          name="deepScan"
                          color="primary"
                        />
                      }
                      label="Enable Deep Scanning"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={appSettings.useAI}
                          onChange={handleAppSettingChange}
                          name="useAI"
                          color="primary"
                        />
                      }
                      label="Use AI for Enhanced Detection"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={appSettings.telemetry}
                          onChange={handleAppSettingChange}
                          name="telemetry"
                          color="primary"
                        />
                      }
                      label="Share Anonymous Usage Data"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Paper>

          <Paper elevation={3} sx={{ borderRadius: 2, p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Security Settings
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              Enabling two-factor authentication significantly improves your account security.
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={securitySettings.twoFactorAuth}
                      onChange={handleSecuritySettingChange}
                      name="twoFactorAuth"
                      color="primary"
                    />
                  }
                  label="Enable Two-Factor Authentication"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel id="password-expiry-label">Password Expiry</InputLabel>
                  <Select
                    labelId="password-expiry-label"
                    id="password-expiry"
                    value={securitySettings.passwordExpiry}
                    label="Password Expiry"
                    name="passwordExpiry"
                    onChange={handleSecuritySettingChange}
                  >
                    <MenuItem value={30}>30 days</MenuItem>
                    <MenuItem value={60}>60 days</MenuItem>
                    <MenuItem value={90}>90 days</MenuItem>
                    <MenuItem value={180}>180 days</MenuItem>
                    <MenuItem value={365}>365 days</MenuItem>
                    <MenuItem value={0}>Never</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  API Access
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={securitySettings.apiKeyEnabled}
                      onChange={handleSecuritySettingChange}
                      name="apiKeyEnabled"
                      color="primary"
                    />
                  }
                  label="Enable API Access"
                />
                
                {securitySettings.apiKeyEnabled && (
                  <Box sx={{ mt: 2 }}>
                    <TextField
                      fullWidth
                      label="API Key"
                      value={securitySettings.apiKey}
                      InputProps={{
                        readOnly: true,
                        endAdornment: (
                          <InputAdornment position="end">
                            <Tooltip title="Generate new API key">
                              <IconButton
                                edge="end"
                                onClick={handleGenerateApiKey}
                              >
                                <Refresh />
                              </IconButton>
                            </Tooltip>
                          </InputAdornment>
                        ),
                      }}
                      variant="outlined"
                      margin="normal"
                    />
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      Keep your API key secure. Regenerating will invalidate the previous key.
                    </Alert>
                  </Box>
                )}
              </Grid>
            </Grid>
          </Paper>

          <Paper elevation={3} sx={{ borderRadius: 2, p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Notification Preferences
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.threatAlerts}
                      onChange={handleNotificationSettingChange}
                      name="threatAlerts"
                      color="primary"
                    />
                  }
                  label="Threat Detection Alerts"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.scanCompletionAlerts}
                      onChange={handleNotificationSettingChange}
                      name="scanCompletionAlerts"
                      color="primary"
                    />
                  }
                  label="Scan Completion Notifications"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.updateNotifications}
                      onChange={handleNotificationSettingChange}
                      name="updateNotifications"
                      color="primary"
                    />
                  }
                  label="Software Update Notifications"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.marketingEmails}
                      onChange={handleNotificationSettingChange}
                      name="marketingEmails"
                      color="primary"
                    />
                  }
                  label="Marketing and Newsletter Emails"
                />
              </Grid>
            </Grid>
          </Paper>

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<Save />}
              onClick={handleSaveSettings}
              size="large"
            >
              Save All Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Settings;