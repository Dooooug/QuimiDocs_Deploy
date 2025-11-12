// src/pages/Dashboard/DashboardPage.js

import React, { useState, useEffect } from 'react';
// Importa os estilos CSS para o layout de Grid
import '../../styles/DashboardPage.css';
// Importa o serviço que faz a chamada à API do backend (Flask)
import dashboardService from '../../services/dashboardService';

// --- IMPORTAÇÕES DOS COMPONENTES DE GRÁFICO ---

// Gráficos Existentes
import ProductStatusChart from '../../components/Dashboard/ProductStatusChart'; // Distribuição por Status

// NOVOS Gráficos (Baseado nas novas agregações do backend)
import ProductsByCompanyChart from '../../components/Dashboard/ProductsByCompanyChart'; // Gráfico de Produtos por Empresa
import PictogramChart from '../../components/Dashboard/PictogramChart'; // Gráfico de Pictogramas de Perigo
import PhysicalStateChart from '../../components/Dashboard/PhysicalStateChart'; // Gráfico de Estado Físico
import DangerClassificationChart from '../../components/Dashboard/DangerClassificationChart'; // Gráfico de Classificação de Perigo
import StorageByCompanyChart from '../../components/Dashboard/StorageByCompanyChart'; // NOVO: Quantidade Armazenada por Empresa/Estado

function DashboardPage() {
    // Estado para armazenar os dados de estatísticas retornados pela API
    const [stats, setStats] = useState(null);
    // Estado para controlar o estado de carregamento
    const [loading, setLoading] = useState(true);
    // Estado para armazenar qualquer mensagem de erro
    const [error, setError] = useState(null);

    // Hook useEffect para buscar os dados quando o componente for montado
    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                setError(null);
                
                // Chamada ao serviço para buscar as estatísticas
                const data = await dashboardService.getDashboardStats();
                
                // Atualiza o estado com os dados recebidos
                setStats(data); 

            } catch (err) {
                // Captura e formata a mensagem de erro
                const errorMessage = err.response?.data?.msg || err.message || 'Falha ao buscar dados';
                setError(errorMessage); 
            
            } finally {
                // Garante que o estado de carregamento seja desativado, independente do sucesso/falha
                setLoading(false);
            }
        };

        fetchDashboardData(); 
    }, []); // O array vazio assegura que o useEffect rode apenas na montagem

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
        // Container principal que define o layout de grid (DashboardPage.css)
        <div className="dashboard-grid-parent"> 

            {/* Área do Título (grid-area: 1 / 1 / 2 / 5) */}
            <div className="dashboard-title-area">
                <h1>Dashboard</h1>
                <p>Bem-vindo ao seu painel de Informações</p>
            </div>

            {/* --- LINHA 1: CARDS E NOVO GRÁFICO --- */}
            
            {/* Card 1: Total de Produtos Cadastrados (div1) */}
            <div className="dashboard-item div1">
                <h2>Produtos Cadastrados</h2>
                <p className="dashboard-stat-number">{stats?.total_products || 0}</p>
            </div>
            
            {/* Card 2: Último Produto Aprovado (div2) */}
            <div className="dashboard-item div2">
                <h2>Último Produto Aprovado</h2>
                <p className="dashboard-stat-text">{stats?.last_approved_product || '-'}</p>
            </div>
            
            {/* Gráfico 6 (movido): Classificação de Perigo (div10) */}
            <div className="dashboard-item dashboard-chart div3">
                <h2>Classificação por Tipo de Perigo</h2>
                <DangerClassificationChart data={stats?.danger_classification || []} />
            </div>

                      
            {/* Gráfico 1: Produtos por Status (div7) - Agora ocupa a primeira coluna da segunda linha */}
            <div className="dashboard-item dashboard-chart div7">
                <h2>Distribuição de Produtos por Status</h2>
                <ProductStatusChart data={stats?.products_by_status || []} />
            </div>

            {/* Gráfico 3 (movido): Produtos por Empresa (div5) - Ocupa a segunda coluna da segunda linha */}
            <div className="dashboard-item dashboard-chart div5">
                <h2>Produtos Cadastrados por Empresa</h2>
                <ProductsByCompanyChart data={stats?.products_by_company || []} />
            </div>
            

            {/* --- LINHA 3: GRÁFICOS 4 E 5 --- */}
            
            {/* Gráfico 4 (movido): Pictogramas de Perigo (div6) */}
            <div className="dashboard-item dashboard-chart div6">
                <h2>Quantidade de Produtos por GHS</h2>
                <PictogramChart data={stats?.products_by_pictogram || []} />
            </div>

            {/* Gráfico 5 (movido): Estado Físico (div8) */}
            <div className="dashboard-item dashboard-chart div8">
                <h2>Distribuição por Estado Físico</h2>
                <PhysicalStateChart data={stats?.products_by_physical_state || []} />
            </div>
            
            {/* NOVO GRÁFICO (div3): Quantidade Armazenada por Empresa por Estado Físico */}
            {/* Este novo gráfico ocupa o espaço ao lado dos dois cards na mesma linha */}
            <div className="dashboard-item dashboard-chart div10">
                <h2>Quantidade Armazenada por Empresa por Estado Físico</h2>
                <StorageByCompanyChart data={stats?.storage_by_company_and_state || []} />
            </div>
                      
            

        </div>
    );
}

export default DashboardPage;