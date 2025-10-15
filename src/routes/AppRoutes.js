// src/routes/AppRoutes.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './PrivateRoute';
import RoleBasedRoute from './RoleBasedRoute';
import { AuthProvider } from '../context/authContext';
import { ROLES } from '../utils/constants';

// Importação dos componentes globais e páginas
import AppLayout from '../components/Layout/AppLayout';
import LoginPage from '../pages/Auth/LoginPage';
import RegisterPage from '../pages/Auth/RegisterPage';
import MainContentPage from '../pages/Home/MainContentPage';
import DashboardPage from '../pages/Dashboard/DashboardPage';
import ProductRegistrationPage from '../pages/Products/ProductRegistrationPage';
import ProductListPage from '../pages/Products/ProductListPage';
import ProductEditPage from '../pages/Products/ProductEditPage';
import FDSPage from '../pages/Products/FDSPage';
import ProductApprovalPage from '../pages/Products/ProductApprovalPage';
import UserManagement from '../pages/Users/UserManagement';
import AccountPage from '../pages/Account/AccountPage';

const AppRoutes = () => {
  return (
    <Router>
      <AuthProvider>
    
        <Routes>
          {/* Rotas Públicas */}
          <Route path="/" element={<MainContentPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Rotas Protegidas que usam o AppLayout com Sidebar */}
          <Route element={<PrivateRoute />}>
            <Route path="/app/*" element={<AppLayout />}>
              {/* Redireciona /app para /app/dashboard */}
              <Route path="" element={<Navigate to="dashboard" replace />} />

              <Route path="dashboard" element={<DashboardPage />} />

              <Route element={<RoleBasedRoute allowedRoles={[ROLES.ADMIN, ROLES.ANALYST]} />}>
                <Route path="product-registration" element={<ProductRegistrationPage />} />
              </Route>

              <Route path="product-list" element={<ProductListPage />} />

              <Route element={<RoleBasedRoute allowedRoles={[ROLES.ADMIN, ROLES.ANALYST]} />}>
                <Route path="products/edit/:id" element={<ProductEditPage />} />
              </Route>

              <Route path="fds" element={<FDSPage />} />

              <Route element={<RoleBasedRoute allowedRoles={[ROLES.ADMIN]} />}>
                <Route path="product-approval" element={<ProductApprovalPage />} />
              </Route>

              <Route element={<RoleBasedRoute allowedRoles={[ROLES.ADMIN]} />}>
                <Route path="users" element={<UserManagement />} />
              </Route>

              <Route path="account" element={<AccountPage />} />

              <Route path="*" element={<h1>Página Interna Não Encontrada</h1>} />
            </Route>
          </Route>

          {/* Página 404 global */}
          <Route path="*" element={<h1>404 - Página Não Encontrada</h1>} />
        </Routes>
      </AuthProvider>
    </Router>
  );
};

export default AppRoutes;
