import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

const scanService = {
  // Upload and scan a file
  scanFile: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/scanner/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onProgress,
    });
  },
  
  // Get scan result details
  getScanResult: (scanId) => {
    return api.get(`/scanner/results/${scanId}/`);
  },
  
  // Get scan threats
  getScanThreats: (scanId) => {
    return api.get(`/scanner/results/${scanId}/threats/`);
  },
  
  // Get scan history
  getScanHistory: (params = {}) => {
    return api.get('/scanner/results/', { params });
  },
  
  // Get scan status
  getScanStatus: (scanId) => {
    return api.get(`/scanner/results/${scanId}/status/`);
  },
  
  // Download scan report as PDF or JSON
  downloadReport: (scanId, format = 'pdf') => {
    return api.get(`/scanner/results/${scanId}/report/`, {
      params: { format },
      responseType: 'blob',
    });
  },
  
  // Get scan statistics
  getStatistics: () => {
    return api.get('/scanner/stats/');
  },
  
  // Delete a scan record
  deleteScan: (scanId) => {
    return api.delete(`/scanner/results/${scanId}/`);
  },
  
  // Get YARA rules
  getYaraRules: () => {
    return api.get('/scanner/yara-rules/');
  },
  
  // Create YARA rule
  createYaraRule: (ruleData) => {
    return api.post('/scanner/yara-rules/', ruleData);
  },
  
  // PCAP Analysis Methods
  uploadPcapFile: (file, options = {}) => {
    const formData = new FormData();
    formData.append('pcap_file', file);
    
    return api.post('/scanner/network-scan/upload_pcap/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onProgress,
    });
  },

  // Get network scan result
  getNetworkScanResult: (scanId) => {
    return api.get(`/scanner/network-scan/${scanId}/`);
  },

  // Get network statistics
  getNetworkStatistics: (scanId) => {
    return api.get(`/scanner/network-scan/${scanId}/statistics/`);
  },

  // Get network threats
  getNetworkThreats: (scanId) => {
    return api.get(`/scanner/network-scan/${scanId}/threats/`);
  },

  // Get AI insights for network analysis
  getAiInsights: (scanId) => {
    return api.get(`/scanner/network-scan/${scanId}/ai_insights/`);
  },

  // Get network scan history
  getNetworkScanHistory: (params = {}) => {
    return api.get('/scanner/network-scan/', { params });
  },

  // Start real-time network monitoring
  startRealtimeMonitoring: (options = {}) => {
    return api.post('/scanner/unified-scan/start_realtime_monitoring/', options);
  },

  // Get unified scan status (for both file and network scans)
  getUnifiedScanStatus: (scanId, scanType) => {
    return api.get(`/scanner/unified-scan/unified_status/`, {
      params: { scan_id: scanId, scan_type: scanType }
    });
  },

  // Upload and scan with unified scanner (auto-detects file type)
  unifiedScan: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/scanner/unified-scan/upload_and_scan/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onProgress,
    });
  },
};

export default scanService;