import React from 'react';
import { Box, Skeleton, Card, CardContent, Grid, styled } from '@mui/material';

// Discord-inspired skeleton components
const SkeletonCard = styled(Card)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#2f3136' : '#f6f6f6',
  border: `1px solid ${theme.palette.mode === 'dark' ? '#40444b' : '#e3e5e8'}`,
  borderRadius: '8px',
  transition: 'all 0.2s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.palette.mode === 'dark' 
      ? '0 8px 16px rgba(0, 0, 0, 0.4)' 
      : '0 8px 16px rgba(0, 0, 0, 0.1)',
  },
}));

const SkeletonContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  '& .MuiSkeleton-root': {
    backgroundColor: theme.palette.mode === 'dark' ? '#40444b' : '#e1e1e1',
    '&::after': {
      background: theme.palette.mode === 'dark' 
        ? 'linear-gradient(90deg, transparent, rgba(114, 137, 218, 0.2), transparent)'
        : 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent)',
    },
  },
}));

// Dashboard skeleton loader
export const DashboardSkeleton = () => {
  return (
    <SkeletonContainer>
      {/* Header skeleton */}
      <Box sx={{ mb: 4 }}>
        <Skeleton variant="text" width="40%" height={40} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="60%" height={24} />
      </Box>

      {/* Quick actions skeleton */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} sm={6} md={3} key={item}>
            <SkeletonCard>
              <CardContent>
                <Skeleton variant="rectangular" height={40} sx={{ mb: 1 }} />
              </CardContent>
            </SkeletonCard>
          </Grid>
        ))}
      </Grid>

      {/* Stats cards skeleton */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} sm={6} md={3} key={item}>
            <SkeletonCard>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Skeleton variant="circular" width={24} height={24} sx={{ mr: 1 }} />
                  <Skeleton variant="text" width="60%" height={20} />
                </Box>
                <Skeleton variant="text" width="40%" height={32} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="80%" height={16} />
              </CardContent>
            </SkeletonCard>
          </Grid>
        ))}
      </Grid>

      {/* Content sections skeleton */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <SkeletonCard>
            <CardContent>
              <Skeleton variant="text" width="30%" height={24} sx={{ mb: 2 }} />
              {[1, 2, 3, 4].map((item) => (
                <Box key={item} sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Skeleton variant="circular" width={12} height={12} sx={{ mr: 2 }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Skeleton variant="text" width="70%" height={20} sx={{ mb: 0.5 }} />
                    <Skeleton variant="text" width="50%" height={16} />
                  </Box>
                  <Skeleton variant="text" width="15%" height={16} />
                </Box>
              ))}
            </CardContent>
          </SkeletonCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <SkeletonCard>
            <CardContent>
              <Skeleton variant="text" width="40%" height={24} sx={{ mb: 2 }} />
              {[1, 2, 3, 4, 5].map((item) => (
                <Box key={item} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Skeleton variant="text" width="60%" height={16} />
                    <Skeleton variant="text" width="20%" height={16} />
                  </Box>
                  <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 1 }} />
                </Box>
              ))}
            </CardContent>
          </SkeletonCard>
        </Grid>
      </Grid>
    </SkeletonContainer>
  );
};

// List skeleton loader
export const ListSkeleton = ({ items = 5 }) => {
  return (
    <SkeletonContainer>
      {Array.from({ length: items }).map((_, index) => (
        <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 2, p: 2 }}>
          <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
          <Box sx={{ flexGrow: 1 }}>
            <Skeleton variant="text" width="70%" height={20} sx={{ mb: 0.5 }} />
            <Skeleton variant="text" width="50%" height={16} />
          </Box>
          <Skeleton variant="rectangular" width={80} height={32} sx={{ borderRadius: 1 }} />
        </Box>
      ))}
    </SkeletonContainer>
  );
};

// Card skeleton loader
export const CardSkeleton = ({ count = 1 }) => {
  return (
    <Grid container spacing={2}>
      {Array.from({ length: count }).map((_, index) => (
        <Grid item xs={12} sm={6} md={4} key={index}>
          <SkeletonCard>
            <CardContent>
              <Skeleton variant="rectangular" height={120} sx={{ mb: 2, borderRadius: 1 }} />
              <Skeleton variant="text" width="80%" height={24} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="60%" height={16} sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Skeleton variant="text" width="30%" height={16} />
                <Skeleton variant="text" width="25%" height={16} />
              </Box>
            </CardContent>
          </SkeletonCard>
        </Grid>
      ))}
    </Grid>
  );
};

// Table skeleton loader
export const TableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <SkeletonContainer>
      {/* Table header */}
      <Box sx={{ display: 'flex', mb: 2, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Box key={index} sx={{ flex: 1, mr: 2 }}>
            <Skeleton variant="text" width="80%" height={20} />
          </Box>
        ))}
      </Box>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box key={rowIndex} sx={{ display: 'flex', mb: 1.5, alignItems: 'center' }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Box key={colIndex} sx={{ flex: 1, mr: 2 }}>
              <Skeleton 
                variant="text" 
                width={colIndex === 0 ? "90%" : "70%"} 
                height={16} 
              />
            </Box>
          ))}
        </Box>
      ))}
    </SkeletonContainer>
  );
};

export default {
  DashboardSkeleton,
  ListSkeleton,
  CardSkeleton,
  TableSkeleton,
};