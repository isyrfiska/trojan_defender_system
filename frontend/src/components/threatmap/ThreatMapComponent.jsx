import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Refresh,
  Fullscreen,
  FilterList,
  Timeline,
  Warning,
  Security,
  BugReport,
  Computer,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom threat icons
const createThreatIcon = (severity, threatType) => {
  const colors = {
    critical: '#f44336',
    high: '#ff9800',
    medium: '#ffeb3b',
    low: '#2196f3',
  };
  
  const color = colors[severity] || '#9e9e9e';
  
  return L.divIcon({
    className: 'custom-threat-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        color: white;
        font-weight: bold;
        animation: pulse 2s infinite;
      ">
        ${threatType.charAt(0).toUpperCase()}
      </div>
      <style>
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.7; }
          100% { transform: scale(1); opacity: 1; }
        }
      </style>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Heat layer component
const HeatLayer = ({ heatData, map }) => {
  const heatLayerRef = useRef(null);
  
  useEffect(() => {
    if (!map || !heatData || heatData.length === 0) return;
    
    // Remove existing heat layer
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
    }
    
    // Create new heat layer
    const heatPoints = heatData.map(point => [
      point.lat,
      point.lng,
      point.intensity || 0.5
    ]);
    
    heatLayerRef.current = L.heatLayer(heatPoints, {
      radius: 25,
      blur: 15,
      maxZoom: 17,
      gradient: {
        0.0: '#313695',
        0.25: '#4575b4',
        0.5: '#74add1',
        0.75: '#fee090',
        1.0: '#d73027'
      }
    }).addTo(map);
    
    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
      }
    };
  }, [map, heatData]);
  
  return null;
};

// Map controller component
const MapController = ({ center, zoom, onMapReady }) => {
  const map = useMap();
  
  useEffect(() => {
    if (onMapReady) {
      onMapReady(map);
    }
  }, [map, onMapReady]);
  
  useEffect(() => {
    if (center && zoom) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom]);
  
  return null;
};

const ThreatMapComponent = ({
  threatData = [],
  heatData = [],
  loading = false,
  onRefresh,
  onFilterChange,
  filters = {},
  statistics = {},
  realTimeEnabled = true,
  onThreatClick,
}) => {
  const theme = useTheme();
  const [map, setMap] = useState(null);
  const [showHeatMap, setShowHeatMap] = useState(true);
  const [mapCenter, setMapCenter] = useState([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Handle map ready
  const handleMapReady = useCallback((mapInstance) => {
    setMap(mapInstance);
  }, []);
  
  // Handle threat marker click
  const handleThreatClick = useCallback((threat) => {
    setSelectedThreat(threat);
    if (onThreatClick) {
      onThreatClick(threat);
    }
  }, [onThreatClick]);
  
  // Handle filter changes
  const handleFilterChange = useCallback((filterType, value) => {
    if (onFilterChange) {
      onFilterChange({ ...filters, [filterType]: value });
    }
  }, [filters, onFilterChange]);
  
  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);
  
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
    <Box sx={{ height: isFullscreen ? '100vh' : '600px', position: 'relative' }}>
      {/* Map Controls */}
      <Paper
        elevation={3}
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 1000,
          p: 2,
          minWidth: 300,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Threat Map Controls
            </Typography>
          </Grid>
          
          {/* Time Range Filter */}
          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Time Range</InputLabel>
              <Select
                value={filters.days || 1}
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
          
          {/* Threat Type Filter */}
          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Threat Type</InputLabel>
              <Select
                value={filters.threat_type || ''}
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
          
          {/* Severity Filter */}
          <Grid item xs={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Severity</InputLabel>
              <Select
                value={filters.severity || ''}
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
          
          {/* Heat Map Toggle */}
          <Grid item xs={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={showHeatMap}
                  onChange={(e) => setShowHeatMap(e.target.checked)}
                  size="small"
                />
              }
              label="Heat Map"
            />
          </Grid>
          
          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Refresh Data">
                <IconButton onClick={onRefresh} disabled={loading} size="small">
                  <Refresh />
                </IconButton>
              </Tooltip>
              <Tooltip title="Toggle Fullscreen">
                <IconButton onClick={toggleFullscreen} size="small">
                  <Fullscreen />
                </IconButton>
              </Tooltip>
              <Chip
                label={`${threatData.length} Threats`}
                color="primary"
                size="small"
              />
              {realTimeEnabled && (
                <Chip
                  label="Live"
                  color="success"
                  size="small"
                  sx={{ animation: 'pulse 2s infinite' }}
                />
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Statistics Panel */}
      {statistics && Object.keys(statistics).length > 0 && (
        <Paper
          elevation={3}
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            zIndex: 1000,
            p: 2,
            minWidth: 250,
            backgroundColor: theme.palette.background.paper,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Threat Statistics
          </Typography>
          
          {statistics.by_severity && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                By Severity
              </Typography>
              {statistics.by_severity.map((item) => (
                <Box key={item.severity} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Chip
                    label={item.severity}
                    size="small"
                    sx={{ backgroundColor: getSeverityColor(item.severity), color: 'white' }}
                  />
                  <Typography variant="body2">{item.count}</Typography>
                </Box>
              ))}
            </Box>
          )}
          
          {statistics.by_type && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                By Type
              </Typography>
              {statistics.by_type.slice(0, 5).map((item) => (
                <Box key={item.threat_type} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {getThreatTypeIcon(item.threat_type)}
                    <Typography variant="body2">{item.threat_type}</Typography>
                  </Box>
                  <Typography variant="body2">{item.count}</Typography>
                </Box>
              ))}
            </Box>
          )}
        </Paper>
      )}
      
      {/* Loading Overlay */}
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
          }}
        >
          <CircularProgress />
        </Box>
      )}
      
      {/* Map Container */}
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        scrollWheelZoom={true}
      >
        <MapController
          center={mapCenter}
          zoom={mapZoom}
          onMapReady={handleMapReady}
        />
        
        {/* Tile Layer */}
        <TileLayer
          url={theme.palette.mode === 'dark' 
            ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          }
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {/* Heat Layer */}
        {showHeatMap && map && (
          <HeatLayer heatData={heatData} map={map} />
        )}
        
        {/* Threat Markers */}
        {threatData.map((threat) => (
          <Marker
            key={threat.id}
            position={[threat.lat, threat.lng]}
            icon={createThreatIcon(threat.severity, threat.threat_type)}
            eventHandlers={{
              click: () => handleThreatClick(threat),
            }}
          >
            <Popup>
              <Card sx={{ minWidth: 250 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {threat.threat_type.charAt(0).toUpperCase() + threat.threat_type.slice(1)} Threat
                  </Typography>
                  
                  <Box sx={{ mb: 1 }}>
                    <Chip
                      label={threat.severity}
                      size="small"
                      sx={{ 
                        backgroundColor: getSeverityColor(threat.severity),
                        color: 'white',
                        mr: 1
                      }}
                    />
                    <Chip
                      label={threat.threat_type}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Location:</strong> {threat.city ? `${threat.city}, ` : ''}{threat.country}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Time:</strong> {new Date(threat.timestamp).toLocaleString()}
                  </Typography>
                  
                  {threat.ip_address && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <strong>IP:</strong> {threat.ip_address}
                    </Typography>
                  )}
                  
                  {threat.file_name && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <strong>File:</strong> {threat.file_name}
                    </Typography>
                  )}
                  
                  {threat.description && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Description:</strong> {threat.description}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {/* No Data Message */}
      {!loading && threatData.length === 0 && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1000,
          }}
        >
          <Alert severity="info">
            No threat data available for the selected filters.
          </Alert>
        </Box>
      )}
    </Box>
  );
};

export default ThreatMapComponent;