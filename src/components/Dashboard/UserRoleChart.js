// src/components/Dashboard/UserRoleChart.js

import React from 'react';
// Importamos os elementos necessários para o gráfico de Barras
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

// 1. Registra os elementos necessários para o gráfico de Barras
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Cores para o dashboard
const BAR_COLOR = 'rgba(54, 162, 235, 0.8)'; // Azul
const BORDER_COLOR = 'rgba(54, 162, 235, 1)';

// O componente recebe os dados da API via props
const UserRoleChart = ({ data }) => {
    // 2. Transforma os dados da API (formato: [{_id: "role", count: 5}])
    const chartData = {
        labels: data.map(item => item._id), // Rótulos: 'Admin', 'Analista', 'Usuário'
        datasets: [
            {
                label: 'Número de Usuários',
                data: data.map(item => item.count), // Valores: 5, 20, 50
                backgroundColor: BAR_COLOR,
                borderColor: BORDER_COLOR,
                borderWidth: 1,
            },
        ],
    };

    // Opções de configuração
    const options = {
        responsive: true,
        maintainAspectRatio: false, // Importante para se ajustar à div9
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
                // Garantir que os rótulos sejam números inteiros
                ticks: {
                    precision: 0
                }
            }
        }
    };

    if (!data || data.length === 0) {
        return <p>Sem dados de cargos de usuários para exibir.</p>;
    }

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default UserRoleChart;