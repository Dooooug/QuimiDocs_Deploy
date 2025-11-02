// src/pages/Dashboard/DashboardPage.js

import React, { useState, useEffect } from 'react';
import '../../styles/DashboardPage.css'; 
import dashboardService from '../../services/dashboardService';

// 1. IMPORTAÇÃO DOS NOVOS COMPONENTES DE GRÁFICO (CAMINHO ATUALIZADO)
import ProductStatusChart from '../../components/Dashboard/ProductStatusChart'; 
import UserRoleChart from '../../components/Dashboard/UserRoleChart'; 

function DashboardPage() {
  
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true); 
        setError(null);   
        
        const data = await dashboardService.getDashboardStats();
        
        setStats(data); 

      } catch (err) {
        const errorMessage = err.response?.data?.msg || err.message || 'Falha ao buscar dados';
        setError(errorMessage); 
      
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData(); 
  }, []); 

  // --- Renderização Condicional (loading e error) ---

  if (loading) {
    return (
      <div className="dashboard-grid-parent">
        <div className="dashboard-title-area">
          <h1>Dashboard</h1>
          <p>Carregando informações...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-grid-parent">
        <div className="dashboard-title-area">
          <h1>Dashboard</h1>
          <p style={{ color: 'red' }}>Erro ao carregar dados: {error}</p>
        </div>
      </div>
    );
  }
  // ----------------------------------------------------

  // Renderização Principal (SUCESSO)
  return (
    <div className="dashboard-grid-parent"> 

      <div className="dashboard-title-area">
        <h1>Dashboard</h1>
        <p>Bem-vindo ao seu painel de Informações</p>
      </div>

      {/* Cards Dinâmicos (div1 a div4) ... (mantidos) */}
      <div className="dashboard-item div1">
        <h2>Produtos Cadastrados</h2>
        <p className="dashboard-stat-number">{stats?.total_products || 0}</p>
      </div>
      <div className="dashboard-item div2">
        <h2>Último Produto Aprovado</h2>
        <p className="dashboard-stat-text">{stats?.last_approved_product || '-'}</p>
      </div>
      <div className="dashboard-item div3">
        <h2>Usuários Cadastrados</h2>
        <p className="dashboard-stat-number">{stats?.total_users || 0}</p>
      </div>
      <div className="dashboard-item div4">
        <h2>Último Usuário Registrado</h2>
        <p className="dashboard-stat-text">{stats?.last_registered_user || '-'}</p>
      </div>


      {/* Área 3: GRÁFICOS REAIS */}
      <div className="dashboard-item dashboard-chart div7">
        <h2>Distribuição de Produtos por Status</h2>
        {/* Gráfico de Rosca/Pizza */}
        <ProductStatusChart data={stats?.products_by_status || []} />
      </div>

      <div className="dashboard-item dashboard-chart div9">
        <h2>Distribuição de Usuários por Nível</h2>
        {/* Gráfico de Barras */}
        <UserRoleChart data={stats?.users_by_role || []} />
      </div>

    </div>
  );
}

export default DashboardPage;