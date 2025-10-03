import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  IconButton,
  FormControlLabel,
  Checkbox,
  TextField,
  Grid,
  Tooltip,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  CardHeader,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CloudUpload,
  NetworkCheck,
  Delete,
  Security,
  Analytics,
  Info,
  Timeline,
  Settings,
  Visibility,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useAlert } from '../hooks/useAlert';
import useWebSocket from '../hooks/useWebSocket';
import scanService from '../services/scanService';

const NetworkScan = () => {
  const navigate = useNavigate();
  const { addAlert } = useAlert();
  const [pcapFiles, setPcapFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  const [scanResult, setScanResult] = useState(null);
  const [networkStats, setNetworkStats] = useState(null);
  const [threats, setThreats] = useState([]);
  const [aiInsights, setAiInsights] = useState(null);
  const [advancedOptions, setAdvancedOptions] = useState(false);
  const [scanOptions, setScanOptions] = useState({
    deepPacketInspection: true,
    protocolAnalysis: true,
    aiThreatDetection: true,
    realTimeMonitoring: false,
    customFilters: '',
  });

  // WebSocket for real-time updates
  const { isConnected, sendMessage } = useWebSocket('/ws/scan-status/');

  const onDrop = useCallback((acceptedFiles) => {
    // Filter for PCAP files only
    const pcapExtensions = ['.pcap', '.pcapng', '.cap'];
    const validFiles = acceptedFiles.filter((file) => {
      const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      return pcapExtensions.includes(extension);
    });
    const invalidFiles = acceptedFiles.filter((file) => {
      const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      return !pcapExtensions.includes(extension);
    });

    if (invalidFiles.length > 0) {
      addAlert({
        message: `${invalidFiles.length} file(s) are not valid PCAP files. Only .pcap, .pcapng, and .cap files are supported.`,
        severity: 'warning',
      });
    }

    // Check file size (max 100MB for PCAP files)
    const maxSize = 100 * 1024 * 1024; // 100MB
    const oversizedFiles = validFiles.filter((file) => file.size > maxSize);
    const acceptableFiles = validFiles.filter((file) => file.size <= maxSize);

    if (oversizedFiles.length > 0) {
      addAlert({
        message: `${oversizedFiles.length} file(s) exceeded the 100MB size limit.`,
        severity: 'warning',
      });
    }

    setPcapFiles((prevFiles) => [
      ...prevFiles,
      ...acceptableFiles.map((file) => ({
        ...file,
        id: Math.random().toString(36).substr(2, 9),
        preview: URL.createObjectURL(file),
      })),
    ]);
  }, [addAlert]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'application/vnd.tcpdump.pcap': ['.pcap'],
      'application/octet-stream': ['.pcapng', '.cap'],
    },
  });

  const handleRemoveFile = (fileId) => {
    setPcapFiles((prevFiles) => {
      const fileToRemove = prevFiles.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return prevFiles.filter(f => f.id !== fileId);
    });
  };

  const handleOptionChange = (event) => {
    const { name, checked, value, type } = event.target;
    setScanOptions((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleScan = async () => {
    if (pcapFiles.length === 0) {
      addAlert({
        message: 'Please add at least one PCAP file to analyze.',
        severity: 'warning',
      });
      return;
    }

    setLoading(true);
    setProgress(0);
    setScanResult(null);
    setNetworkStats(null);
    setThreats([]);
    setAiInsights(null);

    try {
      const scanResults = [];
      
      for (let i = 0; i < pcapFiles.length; i++) {
        const file = pcapFiles[i];
        setProgress(Math.round(((i + 1) / pcapFiles.length) * 100));
        
        // Upload and analyze PCAP file using unified scanner
        const response = await scanService.uploadPcapFile(file, {
          ...scanOptions,
          onProgress: (progressEvent) => {
            const fileProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            const totalProgress = Math.round(((i + fileProgress / 100) / pcapFiles.length) * 100);
            setProgress(totalProgress);
          }
        });
        
        scanResults.push(response.data);
        
        addAlert({
          message: `PCAP file ${file.name} uploaded and analysis initiated.`,
          severity: 'info',
        });
      }
      
      // Get the first scan result for display
      const firstScan = scanResults[0];
      setScanResult(firstScan);
      
      // Fetch additional data
      if (firstScan.scan_id) {
        await fetchNetworkData(firstScan.scan_id);
      }
      
      addAlert({
        message: 'PCAP files uploaded and network analysis initiated successfully!',
        severity: 'success',
      });
    } catch (error) {
      console.error('Network scan error:', error);
      setProgress(0);
      
      let errorMessage = 'Failed to analyze PCAP files. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      addAlert({
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchNetworkData = async (scanId) => {
    try {
      // Fetch network statistics
      const statsResponse = await scanService.getNetworkStatistics(scanId);
      setNetworkStats(statsResponse.data);
      
      // Fetch threats
      const threatsResponse = await scanService.getNetworkThreats(scanId);
      setThreats(threatsResponse.data);
      
      // Fetch AI insights
      const aiResponse = await scanService.getAiInsights(scanId);
      setAiInsights(aiResponse.data);
    } catch (error) {
      console.error('Error fetching network data:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const cleanupPreviews = () => {
    pcapFiles.forEach((file) => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
  };

  useEffect(() => {
    return () => {
      cleanupPreviews();
    };
  }, []);

  const renderUploadSection = () => (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        mb: 4,
        border: '1px dashed',
        borderColor: isDragActive ? 'primary.main' : 'divider',
        backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
        transition: 'all 0.3s ease',
      }}
    >
      <Box
        {...getRootProps()}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: 3,
          cursor: 'pointer',
        }}
      >
        <input {...getInputProps()} />
        <NetworkCheck sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        {isDragActive ? (
          <Typography variant="h6" align="center">
            Drop the PCAP files here...
          </Typography>
        ) : (
          <>
            <Typography variant="h6" align="center" gutterBottom>
              Drag & drop PCAP files here, or click to select files
            </Typography>
            <Typography variant="body2" align="center" color="text.secondary">
              Supported formats: .pcap, .pcapng, .cap (max 100MB per file)
            </Typography>
          </>
        )}
      </Box>
    </Paper>
  );

  const renderFileList = () => {
    if (pcapFiles.length === 0) return null;

    return (
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            PCAP Files ({pcapFiles.length})
          </Typography>
          <Button
            variant="outlined"
            color="error"
            size="small"
            startIcon={<Delete />}
            onClick={() => {
              cleanupPreviews();
              setPcapFiles([]);
            }}
          >
            Clear All
          </Button>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <List>
          {pcapFiles.map((file) => (
            <ListItem
              key={file.id}
              secondaryAction={
                <IconButton edge="end" onClick={() => handleRemoveFile(file.id)}>
                  <Delete />
                </IconButton>
              }
            >
              <ListItemIcon>
                <NetworkCheck />
              </ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB • ${file.type || 'PCAP file'}`}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    );
  };

  const renderScanOptions = () => (
    <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Network Analysis Options
        </Typography>
        <Button
          variant="text"
          startIcon={<Settings />}
          onClick={() => setAdvancedOptions(!advancedOptions)}
        >
          {advancedOptions ? 'Hide Advanced' : 'Show Advanced'}
        </Button>
      </Box>
      <Divider sx={{ mb: 2 }} />

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Checkbox
                checked={scanOptions.deepPacketInspection}
                onChange={handleOptionChange}
                name="deepPacketInspection"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography>Deep Packet Inspection</Typography>
                <Tooltip title="Analyzes packet contents for malicious payloads and suspicious patterns">
                  <Info fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                </Tooltip>
              </Box>
            }
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Checkbox
                checked={scanOptions.protocolAnalysis}
                onChange={handleOptionChange}
                name="protocolAnalysis"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography>Protocol Analysis</Typography>
                <Tooltip title="Examines network protocols for anomalies and security violations">
                  <Info fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                </Tooltip>
              </Box>
            }
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Checkbox
                checked={scanOptions.aiThreatDetection}
                onChange={handleOptionChange}
                name="aiThreatDetection"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography>AI Threat Detection</Typography>
                <Tooltip title="Uses machine learning to identify advanced persistent threats and zero-day attacks">
                  <Info fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                </Tooltip>
              </Box>
            }
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControlLabel
            control={
              <Checkbox
                checked={scanOptions.realTimeMonitoring}
                onChange={handleOptionChange}
                name="realTimeMonitoring"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography>Real-time Monitoring</Typography>
                <Tooltip title="Enables continuous monitoring and alerting for ongoing threats">
                  <Info fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                </Tooltip>
              </Box>
            }
          />
        </Grid>
      </Grid>

      {advancedOptions && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Custom Network Filters (Optional)
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="Enter custom network filters (e.g., BPF filters)..."
            name="customFilters"
            value={scanOptions.customFilters}
            onChange={handleOptionChange}
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <Alert severity="info">
            Custom filters use Berkeley Packet Filter (BPF) syntax for advanced packet filtering.
          </Alert>
        </Box>
      )}
    </Paper>
  );

  const renderResults = () => {
    if (!scanResult) return null;

    return (
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Network Analysis Results
        </Typography>
        
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
          <Tab label="Overview" />
          <Tab label="Network Stats" />
          <Tab label="Threats" />
          <Tab label="AI Insights" />
        </Tabs>

        {activeTab === 0 && renderOverviewTab()}
        {activeTab === 1 && renderNetworkStatsTab()}
        {activeTab === 2 && renderThreatsTab()}
        {activeTab === 3 && renderAiInsightsTab()}
      </Paper>
    );
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Packets
            </Typography>
            <Typography variant="h4">
              {networkStats?.total_packets?.toLocaleString() || '0'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Threats Detected
            </Typography>
            <Typography variant="h4" color={threats.length > 0 ? 'error' : 'success'}>
              {threats.length}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Risk Level
            </Typography>
            <Chip
              label={scanResult.threat_level || 'Unknown'}
              color={scanResult.threat_level === 'high' ? 'error' : scanResult.threat_level === 'medium' ? 'warning' : 'success'}
              size="large"
            />
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Analysis Status
            </Typography>
            <Chip
              label={scanResult.status || 'Unknown'}
              color={scanResult.status === 'completed' ? 'success' : 'info'}
              size="large"
            />
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderNetworkStatsTab = () => {
    if (!networkStats) {
      return (
        <Alert severity="info">
          Network statistics will be available once analysis is complete.
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Protocol Distribution" />
            <CardContent>
              <List>
                {Object.entries(networkStats.protocols || {}).map(([protocol, count]) => (
                  <ListItem key={protocol}>
                    <ListItemText
                      primary={protocol.toUpperCase()}
                      secondary={`${count} packets`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Traffic Summary" />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                Duration: {networkStats.duration || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Data Volume: {networkStats.data_volume || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Unique IPs: {networkStats.unique_ips || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Unique Ports: {networkStats.unique_ports || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderThreatsTab = () => {
    if (threats.length === 0) {
      return (
        <Alert severity="success" icon={<CheckCircle />}>
          No threats detected in the network traffic.
        </Alert>
      );
    }

    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Threat Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Source IP</TableCell>
              <TableCell>Destination IP</TableCell>
              <TableCell>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {threats.map((threat, index) => (
              <TableRow key={index}>
                <TableCell>{threat.threat_type}</TableCell>
                <TableCell>
                  <Chip
                    label={threat.severity}
                    color={threat.severity === 'high' ? 'error' : threat.severity === 'medium' ? 'warning' : 'info'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{threat.source_ip}</TableCell>
                <TableCell>{threat.destination_ip}</TableCell>
                <TableCell>{threat.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderAiInsightsTab = () => {
    if (!aiInsights) {
      return (
        <Alert severity="info">
          AI insights will be available once analysis is complete.
        </Alert>
      );
    }

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader title="AI Threat Analysis" />
            <CardContent>
              <Typography variant="body1" paragraph>
                {aiInsights.summary || 'No AI analysis available.'}
              </Typography>
              {aiInsights.recommendations && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Recommendations:
                  </Typography>
                  <List>
                    {aiInsights.recommendations.map((rec, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Info color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={rec} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Network Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload PCAP files to analyze network traffic, detect threats, and get AI-powered security insights.
      </Typography>

      {renderUploadSection()}
      {renderFileList()}
      {renderScanOptions()}

      {loading && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" sx={{ mr: 1 }}>
              Analyzing network traffic...
            </Typography>
            <Typography variant="body2" color="primary">
              {Math.round(progress)}%
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Analytics />}
          onClick={handleScan}
          disabled={loading || pcapFiles.length === 0}
          sx={{ px: 4, py: 1.5 }}
        >
          {loading ? 'Analyzing...' : 'Start Network Analysis'}
        </Button>
      </Box>

      {renderResults()}

      <Paper elevation={1} sx={{ p: 2, bgcolor: 'background.paper' }}>
        <Typography variant="subtitle2" gutterBottom>
          Network Security Information
        </Typography>
        <Typography variant="body2" color="text.secondary">
          PCAP files are analyzed using advanced packet inspection, protocol analysis, and AI-powered threat detection.
          All network data is processed securely and analysis results are stored in your account history.
        </Typography>
      </Paper>
    </Container>
  );
};

export default NetworkScan;