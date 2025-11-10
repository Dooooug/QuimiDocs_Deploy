// src/components/Dashboard/PhysicalStateChart.js

import React from 'react';
// Importa elementos para o gráfico de Rosca/Pizza
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// 1. Registra os elementos necessários
ChartJS.register(ArcElement, Tooltip, Legend);

// Cores personalizadas para os estados físico
const PHYSICAL_STATE_COLORS = [
    'rgba(54, 162, 235, 0.8)',   // Líquido (Azul)
    'rgba(75, 192, 192, 0.8)',   // Sólido (Ciano/Verde)
    'rgba(153, 102, 255, 0.8)',  // Gasoso (Roxo)
    'rgba(201, 203, 207, 0.8)',  // Outros (Cinza)
];

// Componente recebe os dados da API via props ({_id: "estado_fisico", count: 10})
const PhysicalStateChart = ({ data }) => {
    
    // 2. Transforma os dados da API para o formato do Chart.js
    const chartData = {
        // Rótulos: 'Líquido', 'Sólido', 'Gasoso', etc.
        labels: data.map(item => item._id), 
        datasets: [
            {
                label: 'Total de Produtos',
                // Valores: Contagem de produtos por estado
                data: data.map(item => item.count), 
                backgroundColor: PHYSICAL_STATE_COLORS.slice(0, data.length),
                // Borda mais sólida
                borderColor: PHYSICAL_STATE_COLORS.slice(0, data.length).map(color => color.replace('0.8', '1')), 
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
                position: 'right', // Posiciona a legenda à direita
            },
            title: {
                display: false,
            },
        },
    };

    if (!data || data.length === 0) {
        return <p>Sem dados de estado físico de produtos para exibir.</p>;
    }

    return (
        <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Doughnut data={chartData} options={options} />
        </div>
    );
};

export default PhysicalStateChart;