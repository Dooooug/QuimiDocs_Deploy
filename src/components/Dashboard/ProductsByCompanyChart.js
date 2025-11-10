// src/components/Dashboard/ProductsByCompanyChart.js

import React from 'react';
// Importa elementos para o gráfico de Barras
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// 1. Registra os elementos necessários
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Cores personalizadas (pode ser ajustado)
const BAR_COLOR = 'rgba(255, 99, 132, 0.8)'; // Vermelho claro
const BORDER_COLOR = 'rgba(255, 99, 132, 1)';

// Componente recebe os dados da API via props ({_id: "empresa", count: 50})
const ProductsByCompanyChart = ({ data }) => {
    
    // 2. Transforma os dados da API para o formato do Chart.js
    const chartData = {
        // Rótulos: ID das Empresas
        labels: data.map(item => item._id), 
        datasets: [
            {
                label: 'Número de Produtos',
                // Valores: Contagem de Produtos
                data: data.map(item => item.count), 
                backgroundColor: BAR_COLOR,
                borderColor: BORDER_COLOR,
                borderWidth: 1,
            },
        ],
    };

    // Opções de configuração
    const options = {
        responsive: true,
        maintainAspectRatio: false, 
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: false,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                // Garantir que os rótulos do eixo Y sejam números inteiros
                ticks: {
                    precision: 0
                }
            },
            x: {
                // Ajusta o título para maior legibilidade
                title: {
                    display: true,
                    text: 'Empresa'
                }
            }
        }
    };

    if (!data || data.length === 0) {
        return <p>Sem dados de produtos por empresa para exibir.</p>;
    }

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default ProductsByCompanyChart;