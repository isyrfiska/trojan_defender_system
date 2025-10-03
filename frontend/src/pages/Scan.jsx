import { useState, useRef, useCallback } from 'react';
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
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  Delete,
  Security,
  CheckCircle,
  Info,
  Send,
  Settings,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useAlert } from '../hooks/useAlert';
import scanService from '../services/scanService';

const Scan = () => {
  const navigate = useNavigate();
  const { addAlert } = useAlert();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [advancedOptions, setAdvancedOptions] = useState(false);
  const [scanOptions, setScanOptions] = useState({
    deepScan: true,
    archiveScan: true,
    yaraRules: true,
    aiAnalysis: false,
    customRules: '',
  });

  // For simulating progress in this demo
  const progressInterval = useRef(null);

  const onDrop = useCallback((acceptedFiles) => {
    // Filter out files larger than 50MB
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    const validFiles = acceptedFiles.filter((file) => file.size <= maxSize);
    const oversizedFiles = acceptedFiles.filter((file) => file.size > maxSize);

    if (oversizedFiles.length > 0) {
      addAlert({
        message: `${oversizedFiles.length} file(s) exceeded the 50MB size limit and were not added.`,
        severity: 'warning',
      });
    }

    setFiles((prevFiles) => [
      ...prevFiles,
      ...validFiles.map((file) => Object.assign(file, { preview: URL.createObjectURL(file) })),
    ]);
  }, [addAlert]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const handleRemoveFile = (index) => {
    setFiles((prevFiles) => {
      const newFiles = [...prevFiles];
      // Revoke the object URL to avoid memory leaks
      URL.revokeObjectURL(newFiles[index].preview);
      newFiles.splice(index, 1);
      return newFiles;
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
    if (files.length === 0) {
      addAlert({
        message: 'Please add at least one file to scan.',
        severity: 'warning',
      });
      return;
    }

    setLoading(true);
    setProgress(0);

    try {
      // Process each file sequentially
      const scanResults = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setProgress(Math.round(((i + 1) / files.length) * 100));
        
        // Upload and scan the file
        const response = await scanService.scanFile(file, {
          onProgress: (progressEvent) => {
            const fileProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            const totalProgress = Math.round(((i + fileProgress / 100) / files.length) * 100);
            setProgress(totalProgress);
          }
        });
        
        scanResults.push(response.data);
        
        addAlert({
          message: `File ${file.name} uploaded and scan initiated.`,
          severity: 'info',
        });
      }
      
      // Navigate to the scan result page for the first scan
      const scanId = scanResults[0].scan_id;
      navigate(`/scan-result/${scanId}`);
      
      addAlert({
        message: 'Files uploaded and scanning initiated successfully!',
        severity: 'success',
      });
    } catch (error) {
      console.error('Scan error:', error);
      setProgress(0);
      
      let errorMessage = 'Failed to scan files. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.file) {
        errorMessage = error.response.data.file[0] || errorMessage;
      }
      
      addAlert({
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  // Clean up object URLs when component unmounts
  const cleanupPreviews = () => {
    files.forEach((file) => URL.revokeObjectURL(file.preview));
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Scan Files
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload files to scan for malware, trojans, and other security threats.
      </Typography>

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
          className="dropzone"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: 3,
            cursor: 'pointer',
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          {isDragActive ? (
            <Typography variant="h6" align="center">
              Drop the files here...
            </Typography>
          ) : (
            <>
              <Typography variant="h6" align="center" gutterBottom>
                Drag & drop files here, or click to select files
              </Typography>
              <Typography variant="body2" align="center" color="text.secondary">
                Supported file types: All files (max 50MB per file)
              </Typography>
            </>
          )}
        </Box>
      </Paper>

      {files.length > 0 && (
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Files to Scan ({files.length})
            </Typography>
            <Button
              variant="outlined"
              color="error"
              size="small"
              startIcon={<Delete />}
              onClick={() => {
                cleanupPreviews();
                setFiles([]);
              }}
            >
              Clear All
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <List>
            {files.map((file, index) => (
              <ListItem
                key={index}
                secondaryAction={
                  <IconButton edge="end" aria-label="delete" onClick={() => handleRemoveFile(index)}>
                    <Delete />
                  </IconButton>
                }
              >
                <ListItemIcon>
                  <InsertDriveFile />
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={
                    <>
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                      {file.type && ` • ${file.type}`}
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Scan Options
          </Typography>
          <Button
            variant="text"
            color="primary"
            startIcon={<Settings />}
            onClick={() => setAdvancedOptions(!advancedOptions)}
          >
            {advancedOptions ? 'Hide Advanced Options' : 'Show Advanced Options'}
          </Button>
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={scanOptions.deepScan}
                  onChange={handleOptionChange}
                  name="deepScan"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography>Deep Scan</Typography>
                  <Tooltip title="Performs a thorough analysis of file contents and behavior patterns">
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
                  checked={scanOptions.archiveScan}
                  onChange={handleOptionChange}
                  name="archiveScan"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography>Scan Archives</Typography>
                  <Tooltip title="Extracts and scans files inside archives (zip, rar, etc.)">
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
                  checked={scanOptions.yaraRules}
                  onChange={handleOptionChange}
                  name="yaraRules"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography>Use YARA Rules</Typography>
                  <Tooltip title="Applies advanced pattern matching rules to detect sophisticated threats">
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
                  checked={scanOptions.aiAnalysis}
                  onChange={handleOptionChange}
                  name="aiAnalysis"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography>AI-Enhanced Analysis</Typography>
                  <Tooltip title="Uses machine learning to detect unknown threats and zero-day exploits">
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
              Custom YARA Rules (Optional)
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              placeholder="Paste custom YARA rules here..."
              name="customRules"
              value={scanOptions.customRules}
              onChange={handleOptionChange}
              variant="outlined"
              sx={{ mb: 2 }}
            />
            <Alert severity="info" sx={{ mb: 2 }}>
              Custom YARA rules allow for specialized threat detection. Only use rules from trusted sources.
            </Alert>
          </Box>
        )}
      </Paper>

      {loading && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" sx={{ mr: 1 }}>
              Scanning files...
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
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Security />}
          onClick={handleScan}
          disabled={loading || files.length === 0}
          sx={{ px: 4, py: 1.5 }}
        >
          {loading ? 'Scanning...' : 'Start Scan'}
        </Button>
      </Box>

      <Paper elevation={1} sx={{ p: 2, bgcolor: 'background.paper', mb: 4 }}>
        <Typography variant="subtitle2" gutterBottom>
          Security Information
        </Typography>
        <Typography variant="body2" color="text.secondary">
          All files are scanned using ClamAV and custom YARA rules to detect malware, trojans, ransomware, and other threats.
          Files are processed securely and scan results are stored in your account history.
        </Typography>
      </Paper>
    </Container>
  );
};

export default Scan;