import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import { LoadingSpinner, NotFound, ErrorBoundary, PrivateRoute } from './components/common';
import NetworkMonitor from './components/common/NetworkMonitor';

// Lazy load pages for better performance
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Scan = React.lazy(() => import('./pages/Scan'));
const NetworkScan = React.lazy(() => import('./pages/NetworkScan'));
const ScanHistory = React.lazy(() => import('./pages/ScanHistory'));
const ScanResult = React.lazy(() => import('./pages/ScanResult'));
const ThreatMap = React.lazy(() => import('./pages/ThreatMap'));
const Profile = React.lazy(() => import('./pages/Profile'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const TestLogin = React.lazy(() => import('./pages/TestLogin'));

// Simple Route wrapper without authentication
const SimpleRoute = ({ children }) => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <NetworkMonitor />
      <Routes>
        {/* Layout Route with all routes accessible without authentication */}
        <Route path="/" element={<Layout />}>
          <Route 
            index 
            element={<Navigate to="/dashboard" replace />}
          />
          <Route 
            path="dashboard" 
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            } 
          />
          <Route 
            path="scan" 
            element={
              <PrivateRoute>
                <Scan />
              </PrivateRoute>
            } 
          />
          <Route 
            path="network-scan" 
            element={
              <PrivateRoute>
                <NetworkScan />
              </PrivateRoute>
            } 
          />
          <Route 
            path="scan-history" 
            element={
              <PrivateRoute>
                <ScanHistory />
              </PrivateRoute>
            } 
          />
          <Route 
            path="scan-result/:id" 
            element={
              <PrivateRoute>
                <ScanResult />
              </PrivateRoute>
            } 
          />
          <Route 
            path="threatmap" 
            element={
              <PrivateRoute>
                <ThreatMap />
              </PrivateRoute>
            } 
          />
          <Route 
            path="profile" 
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            } 
          />
          <Route 
            path="settings" 
            element={
              <PrivateRoute>
                <Settings />
              </PrivateRoute>
            } 
          />
          
          {/* Auth Routes */}
          <Route 
            path="login" 
            element={
              <SimpleRoute>
                <Login />
              </SimpleRoute>
            } 
          />
          <Route 
            path="register" 
            element={
              <SimpleRoute>
                <Register />
              </SimpleRoute>
            } 
          />
          <Route 
            path="test-login" 
            element={
              <SimpleRoute>
                <TestLogin />
              </SimpleRoute>
            } 
          />
          
          {/* 404 Route */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;