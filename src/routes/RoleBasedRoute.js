// src/routes/RoleBasedRoute.js
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

function RoleBasedRoute({ allowedRoles }) {
  const { user } = useAuth();

  if (!user || !user.role) {
    return <Navigate to="/login" replace />;
  }

  // Aqui assumimos que allowedRoles já é uma lista de números (ex: [1, 2])
  return allowedRoles.includes(user.role)
    ? <Outlet />
    : <Navigate to="/app/dashboard" replace />;
}

export default RoleBasedRoute;
