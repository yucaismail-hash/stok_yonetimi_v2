// src/routes/AppRoutes.tsx
import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { routeConfigs } from './routeConfig';
import { getLayout } from '../layouts';
import useAuth from '../hooks/useAuth';

// Loading Component
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
    }}
  >
    <CircularProgress />
  </Box>
);

// Private Route Wrapper
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingFallback />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Main App Routes
export default function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {routeConfigs.map((route) => {
          const Layout = getLayout(route.layout || 'app');
          const Component = route.component;

          const RouteElement = (
            <Layout>
              <Component />
            </Layout>
          );

          if (route.requiresAuth) {
            return (
              <Route
                key={route.path}
                path={route.path}
                element={<PrivateRoute>{RouteElement}</PrivateRoute>}
              />
            );
          }

          return (
            <Route
              key={route.path}
              path={route.path}
              element={RouteElement}
            />
          );
        })}

        {/* 404 Not Found */}
        <Route
          path="*"
          element={
            <Layout>
              <div>404 - Sayfa Bulunamadı</div>
            </Layout>
          }
        />
      </Routes>
    </Suspense>
  );
}