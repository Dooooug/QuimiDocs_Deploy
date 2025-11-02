// src/components/Dashboard/ProductStatusChart.js

import React from 'react';
// Importamos os componentes específicos do Chart.js que vamos usar
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// 1. Registra os elementos necessários para o gráfico de Rosca/Pizza
ChartJS.register(ArcElement, Tooltip, Legend);

// Cores personalizadas para o dashboard
const BACKGROUND_COLORS = [
    'rgba(75, 192, 192, 0.6)', // Aprovado (Verde/Azul)
    'rgba(255, 159, 64, 0.6)', // Pendente (Laranja)
    'rgba(255, 99, 132, 0.6)', // Rejeitado (Vermelho)
    'rgba(54, 162, 235, 0.6)', // Outros (Azul)
    'rgba(153, 102, 255, 0.6)',
];

// O componente recebe os dados da API via props
const ProductStatusChart = ({ data }) => {
    // 2. Transforma os dados da API (que é o formato: [{_id: "status", count: 10}])
    const chartData = {
        labels: data.map(item => item._id), // Rótulos: 'aprovado', 'pendente', etc.
        datasets: [
            {
                label: 'Total de Produtos',
                data: data.map(item => item.count), // Valores: 10, 5, 2, etc.
                backgroundColor: BACKGROUND_COLORS.slice(0, data.length),
                borderColor: BACKGROUND_COLORS.slice(0, data.length).map(color => color.replace('0.6', '1')), // Versão mais sólida
                borderWidth: 1,
            },
        ],
    };

    // Opções de configuração
    const options = {
        responsive: true,
        maintainAspectRatio: false, // Importante para se ajustar à div7
        plugins: {
            legend: {
                position: 'right', // Posição da legenda
            },
            title: {
                display: false, // O título será o <h2> no componente pai
            },
        },
    };

    if (!data || data.length === 0) {
        return <p>Sem dados de status de produtos para exibir.</p>;
    }

    return (
        <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Doughnut data={chartData} options={options} />
        </div>
    );
};

export default ProductStatusChart;