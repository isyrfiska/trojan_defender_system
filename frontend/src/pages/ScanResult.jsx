import { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Divider,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Tooltip,
  IconButton,
  LinearProgress,
  Badge,
  Card,
  CardContent,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  ExpandMore,
  InsertDriveFile,
  Download,
  Share,
  Delete,
  Security,
  Chat,
  Refresh,
  Shield,
  BugReport,
  Visibility,
} from '@mui/icons-material';
import scanService from '../services/scanService';
import { useAlert } from '../hooks/useAlert';
import { useScanStatus } from '../hooks/useScanStatus';

const ScanResult = () => {
  const { id: scanId } = useParams();
  const { addAlert } = useAlert();
  const [scanResult, setScanResult] = useState(null);
  const [threats, setThreats] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  
  // Use the scan status hook for real-time updates
  const {
    status,
    threatLevel,
    threatCount,
    progress,
    loading,
    error,
    refreshStatus
  } = useScanStatus(scanId);

  // Fetch detailed scan result when status is completed
  useEffect(() => {
    const fetchScanResult = async () => {
      if (!scanId) return;
      
      try {
        const response = await scanService.getScanResult(scanId);
        setScanResult(response.data);
        
        // Fetch threats if there are any
        if (response.data.threats || threatCount > 0) {
          try {
            const threatsResponse = await scanService.getScanThreats(scanId);
            setThreats(threatsResponse.data);
          } catch (threatError) {
            console.error('Error fetching threats:', threatError);
            // If threats endpoint fails, use threats from scan result if available
            if (response.data.threats) {
              setThreats(response.data.threats);
            }
          }
        }
      } catch (error) {
        console.error('Error fetching scan result:', error);
        addAlert({
          message: 'Failed to fetch scan details. Please try again.',
          severity: 'error',
        });
      }
    };
    
    // Fetch immediately if scan is completed, or when status changes to completed
    if (status === 'completed' || status === 'failed' || !status) {
      fetchScanResult();
    }
  }, [scanId, status, threatLevel, threatCount, addAlert]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      if (refreshStatus) {
        await refreshStatus();
      }
      // Refetch scan result
      const response = await scanService.getScanResult(scanId);
      setScanResult(response.data);
      
      // Refetch threats
      if (response.data.threats || threatCount > 0) {
        try {
          const threatsResponse = await scanService.getScanThreats(scanId);
          setThreats(threatsResponse.data);
        } catch (threatError) {
          console.error('Error fetching threats:', threatError);
          if (response.data.threats) {
            setThreats(response.data.threats);
          }
        }
      }
    } catch (error) {
      console.error('Error refreshing scan result:', error);
      addAlert({
        message: 'Failed to refresh scan result',
        severity: 'error'
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      await scanService.downloadReport(scanId, 'pdf');
      addAlert({
        message: 'Report download started',
        severity: 'success',
      });
    } catch (error) {
      addAlert({
        message: 'Failed to download report',
        severity: 'error',
      });
    }
  };

  const handleDeleteScan = async () => {
    try {
      await scanService.deleteScan(scanId);
      addAlert({
        message: 'Scan record deleted successfully',
        severity: 'success',
      });
      // Navigate back to scan history or dashboard
      window.history.back();
    } catch (error) {
      addAlert({
        message: 'Failed to delete scan record',
        severity: 'error',
      });
    }
  };

  const getThreatLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'clean':
        return 'success';
      case 'low':
        return 'info';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'default';
    }
  };

  const getThreatLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'clean':
        return <CheckCircle color="success" />;
      case 'low':
        return <Info color="info" />;
      case 'medium':
        return <Warning color="warning" />;
      case 'high':
        return <ErrorIcon color="error" />;
      default:
        return <Security color="action" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'low':
        return 'info';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getEngineIcon = (engine) => {
    switch (engine?.toLowerCase()) {
      case 'virustotal':
        return <Shield color="primary" />;
      case 'clamav':
        return <Security color="secondary" />;
      case 'yara':
        return <BugReport color="action" />;
      default:
        return <Visibility color="action" />;
    }
  };

  const getScanStatusColor = () => {
    switch (status) {
      case 'completed': return 'success';
      case 'scanning': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Show loading state
  if (loading && !scanResult) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>
            Loading scan result...
          </Typography>
        </Box>
      </Container>
    );
  }

  // Show error state
  if (error && !scanResult) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
        <Box display="flex" justifyContent="center" mt={2}>
          <Button variant="contained" onClick={handleRefresh}>
            Retry
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Scan Result
      </Typography>
      
      {/* Status and progress section */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Chip 
              label={status || 'Unknown'} 
              color={getScanStatusColor()} 
              variant="outlined"
            />
          </Grid>
          <Grid item>
            <Badge badgeContent={threatCount || threats.length} color="error">
              <Chip 
                icon={getThreatLevelIcon(scanResult?.threat_level || threatLevel)}
                label={`Threat Level: ${(scanResult?.threat_level || threatLevel || 'Unknown').toUpperCase()}`}
                color={getThreatLevelColor(scanResult?.threat_level || threatLevel)}
                variant="outlined"
              />
            </Badge>
          </Grid>
          <Grid item xs>
            {status === 'scanning' && (
              <LinearProgress variant="determinate" value={progress} />
            )}
          </Grid>
          <Grid item>
            <IconButton 
              onClick={handleRefresh} 
              disabled={refreshing}
              size="small"
            >
              <Refresh />
            </IconButton>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Scan result details */}
      {scanResult && (
        <>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              File Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Scan ID:</strong> {scanResult.id}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>File Name:</strong> {scanResult.file_name || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>File Size:</strong> {formatFileSize(scanResult.file_size)}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Scan Date:</strong> {scanResult.scan_date ? new Date(scanResult.scan_date).toLocaleString() : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Scan Duration:</strong> {scanResult.scan_duration ? `${scanResult.scan_duration.toFixed(2)}s` : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                  <strong>File Hash:</strong> {scanResult.file_hash || 'N/A'}
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          {/* Threats section */}
          {threats && threats.length > 0 && (
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="error">
                Detected Threats ({threats.length})
              </Typography>
              <Grid container spacing={2}>
                {threats.map((threat, index) => (
                  <Grid item xs={12} key={threat.id || index}>
                    <Card variant="outlined" sx={{ borderColor: getSeverityColor(threat.severity) === 'error' ? 'error.main' : 'warning.main' }}>
                      <CardContent>
                        <Box display="flex" alignItems="center" mb={1}>
                          {getEngineIcon(threat.detection_engine)}
                          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
                            {threat.name}
                          </Typography>
                          <Chip 
                            label={threat.severity?.toUpperCase() || 'UNKNOWN'}
                            color={getSeverityColor(threat.severity)}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Type:</strong> {threat.threat_type?.replace('_', ' ').toUpperCase() || 'Unknown'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Description:</strong> {threat.description || 'No description available'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Location:</strong> {threat.location || 'Unknown'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Detection Engine:</strong> {threat.detection_engine || 'Unknown'}
                        </Typography>
                        {threat.detection_rule && (
                          <Typography variant="body2" color="text.secondary">
                            <strong>Detection Rule:</strong> {threat.detection_rule}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          )}

          {/* Clean file message */}
          {(!threats || threats.length === 0) && scanResult.threat_level === 'clean' && (
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
              <Box display="flex" alignItems="center" justifyContent="center">
                <CheckCircle color="success" sx={{ fontSize: 48, mr: 2 }} />
                <Box>
                  <Typography variant="h6" color="success.main">
                    File is Clean
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No threats detected by ClamAV, YARA rules, or VirusTotal analysis.
                  </Typography>
                </Box>
              </Box>
            </Paper>
          )}

          {/* Scan engines information */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scan Engines Used
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <Security color="secondary" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="body2"><strong>ClamAV</strong></Typography>
                    <Typography variant="caption" color="text.secondary">
                      Signature-based detection
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <BugReport color="action" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="body2"><strong>YARA Rules</strong></Typography>
                    <Typography variant="caption" color="text.secondary">
                      Pattern matching analysis
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" alignItems="center">
                  <Shield color="primary" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="body2"><strong>VirusTotal</strong></Typography>
                    <Typography variant="caption" color="text.secondary">
                      Multi-engine cloud analysis
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
          
          {/* Action buttons */}
          <Box display="flex" gap={2} justifyContent="center">
            <Button 
              variant="contained" 
              startIcon={<Download />}
              onClick={handleDownloadReport}
            >
              Download Report
            </Button>
            <Button 
              variant="outlined" 
              color="error"
              startIcon={<Delete />}
              onClick={handleDeleteScan}
            >
              Delete Scan
            </Button>
          </Box>
        </>
      )}
    </Container>
  );
};

export default ScanResult;