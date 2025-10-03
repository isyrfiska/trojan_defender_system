import React from 'react';
import { Box, Container, Typography, Grid } from '@mui/material';
import { 
  Security, 
  Map, 
  History, 
  Chat,
  TrendingUp,
  Warning,
  CheckCircle,
  Speed
} from '@mui/icons-material';
import { Card, StatCard, PrimaryButton } from '../common';

const Dashboard = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography 
        variant="h4" 
        component="h1" 
        gutterBottom
        sx={{ 
          fontWeight: 'var(--font-weight-bold)',
          color: 'var(--color-text-primary)',
          mb: 4
        }}
      >
        Security Dashboard
      </Typography>
      
      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="System Status"
            value="Secure"
            subtitle="Last scan: 2 hours ago"
            icon={<CheckCircle />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Threats Detected"
            value="0"
            subtitle="This week"
            icon={<Warning />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Scan Performance"
            value="98%"
            subtitle="Detection rate"
            icon={<Speed />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Security Score"
            value="A+"
            subtitle="Excellent protection"
            icon={<TrendingUp />}
          />
        </Grid>
      </Grid>

      {/* Action Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation="md">
            <Card.Header 
              title="Quick Scan"
              avatar={<Security color="primary" />}
            />
            <Card.Content>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Start a quick security scan of your system
              </Typography>
            </Card.Content>
            <Card.Actions>
              <PrimaryButton size="small" fullWidth>
                Start Scan
              </PrimaryButton>
            </Card.Actions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation="md">
            <Card.Header 
              title="Threat Map"
              avatar={<Map color="primary" />}
            />
            <Card.Content>
              <Typography variant="body2" sx={{ mb: 2 }}>
                View global threat intelligence and patterns
              </Typography>
            </Card.Content>
            <Card.Actions>
              <PrimaryButton size="small" fullWidth>
                View Map
              </PrimaryButton>
            </Card.Actions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation="md">
            <Card.Header 
              title="Scan History"
              avatar={<History color="primary" />}
            />
            <Card.Content>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Review previous scans and security reports
              </Typography>
            </Card.Content>
            <Card.Actions>
              <PrimaryButton size="small" fullWidth>
                View History
              </PrimaryButton>
            </Card.Actions>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation="md">
            <Card.Header 
              title="Security Chat"
              avatar={<Chat color="primary" />}
            />
            <Card.Content>
              <Typography variant="body2" sx={{ mb: 2 }}>
                AI-powered security assistance and guidance
              </Typography>
            </Card.Content>
            <Card.Actions>
              <PrimaryButton size="small" fullWidth>
                Start Chat
              </PrimaryButton>
            </Card.Actions>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;