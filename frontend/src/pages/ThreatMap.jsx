import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  Button,
  Tooltip,
  IconButton,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Refresh,
  Download,
  Timeline,
  Warning,
  Security,
  BugReport,
  Computer,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useAlert } from '../hooks/useAlert';
import threatMapService from '../services/threatMapService';
import ThreatMapComponent from '../components/threatmap/ThreatMapComponent';

const ThreatMap = () => {
  const theme = useTheme();
  const { error: showError, success: showSuccess } = useAlert();
  
  // State management
  const [threatData, setThreatData] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    days: 30,
    threat_type: '',
    severity: '',
    country: '',
  });
  const [lastUpdate, setLastUpdate] = useState(null);

  // Load initial threat map data
  const loadThreatMapData = useCallback(async (currentFilters = filters) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await threatMapService.getMapData(currentFilters);
      
      if (result.success) {
        setThreatData(result.threats);
        setStatistics(result.statistics);
        setLastUpdate(new Date().toISOString());
        showSuccess('Threat map data loaded successfully');
      } else {
        // Provide specific error messages based on error type
        let errorMessage = result.error;
        
        if (result.error?.includes('401') || result.error?.includes('Unauthorized')) {
          errorMessage = 'Authentication failed. Please log in again.';
        } else if (result.error?.includes('429') || result.error?.includes('rate limit')) {
          errorMessage = 'Too many requests. Please wait a moment and try again.';
        } else if (result.error?.includes('500') || result.error?.includes('Internal Server Error')) {
          errorMessage = 'Server error. Please try again later or contact support.';
        } else if (result.error?.includes('Network Error') || result.error?.includes('ECONNREFUSED')) {
          errorMessage = 'Unable to connect to server. Please check your connection.';
        } else if (!result.error) {
          errorMessage = 'Failed to load threatmap - Unknown error occurred';
        }
        
        setError(errorMessage);
        showError(errorMessage);
      }
    } catch (err) {
      console.error('ThreatMap loading error:', err);
      
      // Provide specific error messages for different error types
      let errorMessage = 'Failed to load threatmap';
      
      if (err.response?.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (err.response?.status === 429) {
        errorMessage = 'Rate limit exceeded. Please wait and try again.';
      } else if (err.response?.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        errorMessage = 'Unable to connect to server. Please check your connection.';
      } else if (err.message) {
        errorMessage = `Failed to load threatmap: ${err.message}`;
      }
      
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [filters, showError, showSuccess]);

  // Handle filter changes
  const handleFilterChange = useCallback((filterType, value) => {
    const newFilters = { ...filters, [filterType]: value };
    setFilters(newFilters);
    loadThreatMapData(newFilters);
  }, [filters, loadThreatMapData]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    loadThreatMapData();
  }, [loadThreatMapData]);

  // Handle report generation
  const handleGenerateReport = useCallback(async () => {
    try {
      const result = await threatMapService.generateReport({
        ...filters,
        format: 'json',
        include_charts: true,
        include_statistics: true,
      });
      
      if (result.success) {
        showSuccess('Report generated successfully');
      } else {
        showError(result.error || 'Failed to generate report');
      }
    } catch (err) {
      showError('Failed to generate report');
    }
  }, [filters, showError, showSuccess]);

  // Initial data load
  useEffect(() => {
    loadThreatMapData();
  }, [loadThreatMapData]);

  // Get threat type icon
  const getThreatTypeIcon = (threatType) => {
    const icons = {
      malware: <BugReport />,
      virus: <Security />,
      trojan: <Computer />,
      ransomware: <Warning />,
    };
    return icons[threatType] || <Security />;
  };

  // Get severity color
  const getSeverityColor = (severity) => {
    const colors = {
      critical: theme.palette.error.main,
      high: theme.palette.warning.main,
      medium: theme.palette.info.main,
      low: theme.palette.success.main,
    };
    return colors[severity] || theme.palette.grey[500];
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" component="h1" gutterBottom>
              Global Threat Map
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Real-time visualization of cyber threats worldwide
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <Tooltip title="Refresh Data">
                <IconButton onClick={handleRefresh} disabled={loading}>
                  <Refresh />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Generate Report">
                <IconButton onClick={handleGenerateReport}>
                  <Download />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="View Trends">
                <IconButton>
                  <Timeline />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Filters */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Time Range</InputLabel>
              <Select
                value={filters.days}
                label="Time Range"
                onChange={(e) => handleFilterChange('days', e.target.value)}
              >
                <MenuItem value={1}>Last 24 Hours</MenuItem>
                <MenuItem value={7}>Last Week</MenuItem>
                <MenuItem value={30}>Last Month</MenuItem>
                <MenuItem value={90}>Last 3 Months</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Threat Type</InputLabel>
              <Select
                value={filters.threat_type}
                label="Threat Type"
                onChange={(e) => handleFilterChange('threat_type', e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="malware">Malware</MenuItem>
                <MenuItem value="virus">Virus</MenuItem>
                <MenuItem value="trojan">Trojan</MenuItem>
                <MenuItem value="ransomware">Ransomware</MenuItem>
                <MenuItem value="spyware">Spyware</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Severity</InputLabel>
              <Select
                value={filters.severity}
                label="Severity"
                onChange={(e) => handleFilterChange('severity', e.target.value)}
              >
                <MenuItem value="">All Severities</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <Chip
              label={`${threatData.length} Active Threats`}
              color="primary"
              variant="outlined"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Status Indicators */}
      {lastUpdate && (
        <Box sx={{ mb: 2 }}>
          <Chip
            label={`Updated: ${new Date(lastUpdate).toLocaleTimeString()}`}
            variant="outlined"
          />
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Threat Map Component */}
        <Grid item xs={12} lg={9}>
          <Paper elevation={3} sx={{ height: '600px', position: 'relative' }}>
            {error && (
              <Alert severity="error" sx={{ position: 'absolute', top: 10, left: 10, right: 10, zIndex: 1000 }}>
                {error}
              </Alert>
            )}
            
            <ThreatMapComponent 
              threatData={threatData}
              statistics={statistics}
              loading={loading}
              filters={filters}
              onFilterChange={handleFilterChange}
              onRefresh={handleRefresh}
            />
          </Paper>
        </Grid>

        {/* Statistics Panel */}
        <Grid item xs={12} lg={3}>
          <Grid container spacing={2}>
            {/* Threat Summary */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Threat Summary
                  </Typography>
                  
                  {statistics.by_severity && statistics.by_severity.map((item) => (
                    <Box key={item.severity} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Chip
                        label={item.severity}
                        size="small"
                        sx={{ backgroundColor: getSeverityColor(item.severity), color: 'white' }}
                      />
                      <Typography variant="body2">{item.count}</Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Threat Types */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Threat Types
                  </Typography>
                  
                  {statistics.by_type && statistics.by_type.slice(0, 5).map((item) => (
                    <Box key={item.threat_type} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {getThreatTypeIcon(item.threat_type)}
                        <Typography variant="body2">{item.threat_type}</Typography>
                      </Box>
                      <Typography variant="body2">{item.count}</Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Top Countries */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Top Affected Countries
                  </Typography>
                  
                  {statistics.by_country && statistics.by_country.slice(0, 5).map((item) => (
                    <Box key={item.country} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">{item.country || 'Unknown'}</Typography>
                      <Typography variant="body2">{item.count}</Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ThreatMap;