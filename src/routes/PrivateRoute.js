// src/routes/PrivateRoute.js
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom'; // Importação correta de Navigate e Outlet
import useAuth from '../hooks/useAuth'; // Importação correta do useAuth

function PrivateRoute() {
  const { user, token } = useAuth();

  // Se o usuário NÃO estiver logado ou não houver token, redireciona para a página de login.
  if (!user || !token) {
    return <Navigate to="/login" replace />;
  }

  // Se estiver logado, permite que as rotas aninhadas sejam renderizadas.
  return <Outlet />;
}

export default PrivateRoute;
