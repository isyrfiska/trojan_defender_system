import { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Divider,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Pagination,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  Search,
  Delete,
  Visibility,
  Download,
  FilterList,
  Sort,
  CalendarToday,
} from '@mui/icons-material';
import scanService from '../services/scanService';
import { useAlert } from '../hooks/useAlert';



const ScanHistory = () => {
  const { addAlert } = useAlert();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scanToDelete, setScanToDelete] = useState(null);

  const fetchScanHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await scanService.getScanHistory({
        page,
        limit: rowsPerPage,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        ordering: sortOrder === 'newest' ? '-created_at' : 'created_at',
      });
      
      setScanHistory(response.data?.results || []);
      setFilteredHistory(response.data?.results || []);
      
    } catch (error) {
      console.error('Error fetching scan history:', error);
      setError(error.message || 'Failed to load scan history');
      
      // Set empty data instead of mock data
      setScanHistory([]);
      setFilteredHistory([]);
      
      addAlert({
        message: 'Failed to load scan history. Please try again.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScanHistory();
  }, [page, statusFilter, sortOrder]);

  const handleRetry = () => {
    fetchScanHistory();
  };

  useEffect(() => {
    // Apply filters and search
    let filtered = [...scanHistory];

    // Apply search term
    if (searchTerm) {
      filtered = filtered.filter(scan => 
        scan.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(scan => {
        if (statusFilter === 'clean') return !scan.threatDetected;
        if (statusFilter === 'infected') return scan.threatDetected;
        return true;
      });
    }

    // Apply date filter
    if (dateFilter !== 'all') {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      const lastWeek = new Date(today);
      lastWeek.setDate(lastWeek.getDate() - 7);
      const lastMonth = new Date(today);
      lastMonth.setMonth(lastMonth.getMonth() - 1);

      filtered = filtered.filter(scan => {
        const scanDate = new Date(scan.timestamp);
        if (dateFilter === 'today') {
          return scanDate >= today;
        } else if (dateFilter === 'yesterday') {
          return scanDate >= yesterday && scanDate < today;
        } else if (dateFilter === 'week') {
          return scanDate >= lastWeek;
        } else if (dateFilter === 'month') {
          return scanDate >= lastMonth;
        }
        return true;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const dateA = new Date(a.timestamp);
      const dateB = new Date(b.timestamp);
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    setFilteredHistory(filtered);
    setPage(1); // Reset to first page when filters change
  }, [scanHistory, searchTerm, statusFilter, dateFilter, sortOrder]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleDeleteClick = (scanId) => {
    setScanToDelete(scanId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      // In a real app, this would be an actual API call
      // await scanService.deleteScan(scanToDelete);
      
      // Update local state
      const updatedHistory = scanHistory.filter(scan => scan.id !== scanToDelete);
      setScanHistory(updatedHistory);
      setFilteredHistory(updatedHistory);
      
      addAlert({
        message: 'Scan record deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error deleting scan:', error);
      addAlert({
        message: 'Failed to delete scan record. Please try again.',
        severity: 'error',
      });
    } finally {
      setDeleteDialogOpen(false);
      setScanToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setScanToDelete(null);
  };

  const handleDownloadReport = async (scanId, format = 'pdf') => {
    try {
      addAlert({
        message: 'Generating scan report...',
        severity: 'info',
      });
      
      const response = await scanService.downloadReport(scanId, format);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `scan_report_${scanId}_${timestamp}.${format}`;
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      addAlert({
        message: `Scan report downloaded successfully (${format.toUpperCase()})`,
        severity: 'success',
      });
    } catch (error) {
      console.error('Error downloading report:', error);
      addAlert({
        message: 'Failed to download scan report. Please try again.',
        severity: 'error',
      });
    }
  };

  const getStatusChip = (scan) => {
    if (scan.threatDetected) {
      return (
        <Chip
          icon={<ErrorIcon />}
          label="Threats Detected"
          color="error"
          size="small"
        />
      );
    } else {
      return (
        <Chip
          icon={<CheckCircle />}
          label="Clean"
          color="success"
          size="small"
        />
      );
    }
  };

  // Calculate pagination
  const startIndex = (page - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedHistory = filteredHistory.slice(startIndex, endIndex);
  const totalPages = Math.ceil(filteredHistory.length / rowsPerPage);

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
          Scan History
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and manage your previous scan results
        </Typography>
      </Box>

      {/* Filters and Search */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', mb: 3 }}>
          <TextField
            label="Search by ID"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ flexGrow: 1, minWidth: '200px' }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          
          <FormControl size="small" sx={{ minWidth: '150px' }}>
            <InputLabel id="status-filter-label">Status</InputLabel>
            <Select
              labelId="status-filter-label"
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
              startAdornment={
                <InputAdornment position="start">
                  <FilterList fontSize="small" />
                </InputAdornment>
              }
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="clean">Clean</MenuItem>
              <MenuItem value="infected">Infected</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: '150px' }}>
            <InputLabel id="date-filter-label">Date</InputLabel>
            <Select
              labelId="date-filter-label"
              value={dateFilter}
              label="Date"
              onChange={(e) => setDateFilter(e.target.value)}
              startAdornment={
                <InputAdornment position="start">
                  <CalendarToday fontSize="small" />
                </InputAdornment>
              }
            >
              <MenuItem value="all">All Time</MenuItem>
              <MenuItem value="today">Today</MenuItem>
              <MenuItem value="yesterday">Yesterday</MenuItem>
              <MenuItem value="week">Last 7 Days</MenuItem>
              <MenuItem value="month">Last 30 Days</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: '150px' }}>
            <InputLabel id="sort-order-label">Sort By</InputLabel>
            <Select
              labelId="sort-order-label"
              value={sortOrder}
              label="Sort By"
              onChange={(e) => setSortOrder(e.target.value)}
              startAdornment={
                <InputAdornment position="start">
                  <Sort fontSize="small" />
                </InputAdornment>
              }
            >
              <MenuItem value="newest">Newest First</MenuItem>
              <MenuItem value="oldest">Oldest First</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Scan History Table */}
        {filteredHistory.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No scan records found matching your filters.
            </Typography>
            <Button
              variant="contained"
              component={RouterLink}
              to="/scan"
              sx={{ mt: 2 }}
            >
              Start New Scan
            </Button>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Scan ID</TableCell>
                    <TableCell>Date & Time</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Files</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedHistory.map((scan) => (
                    <TableRow key={scan.id} hover>
                      <TableCell>{scan.id}</TableCell>
                      <TableCell>{new Date(scan.timestamp).toLocaleString()}</TableCell>
                      <TableCell>{getStatusChip(scan)}</TableCell>
                      <TableCell>
                        {scan.summary.totalFiles} files ({scan.summary.totalSize})
                      </TableCell>
                      <TableCell>{scan.summary.scanDuration}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex' }}>
                          <IconButton
                            component={RouterLink}
                            to={`/scan-result/${scan.id}`}
                            size="small"
                            color="primary"
                            title="View Details"
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="primary"
                            title="Download Report"
                            onClick={() => handleDownloadReport(scan.id)}
                          >
                            <Download fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            title="Delete Record"
                            onClick={() => handleDeleteClick(scan.id)}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handleChangePage}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          </>
        )}
      </Paper>

      {/* Summary Stats */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Scan Statistics
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'space-around', mt: 2 }}>
          <Box sx={{ textAlign: 'center', minWidth: '120px' }}>
            <Typography variant="h4">{scanHistory.length}</Typography>
            <Typography variant="body2" color="text.secondary">Total Scans</Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: '120px' }}>
            <Typography variant="h4" color="success.main">
              {scanHistory.filter(scan => !scan.threatDetected).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">Clean Scans</Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: '120px' }}>
            <Typography variant="h4" color="error.main">
              {scanHistory.filter(scan => scan.threatDetected).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">Infected Scans</Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: '120px' }}>
            <Typography variant="h4">
              {scanHistory.reduce((total, scan) => total + scan.summary.totalFiles, 0)}
            </Typography>
            <Typography variant="body2" color="text.secondary">Files Scanned</Typography>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
        <Button
          variant="contained"
          component={RouterLink}
          to="/scan"
          size="large"
        >
          Start New Scan
        </Button>
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this scan record? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ScanHistory;