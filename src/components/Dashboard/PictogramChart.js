// src/components/Dashboard/PictogramChart.js

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

// --- Paleta de Cores Dinâmicas GHS ---
// Estas cores serão ciclicamente aplicadas a cada barra do gráfico.
const GHS_COLORS = [
    'rgba(255, 99, 132, 0.8)',   // Vermelho (Perigo Geral)
    'rgba(54, 162, 235, 0.8)',   // Azul (Gás sob pressão)
    'rgba(255, 206, 86, 0.8)',   // Amarelo (Inflamável)
    'rgba(75, 192, 192, 0.8)',   // Ciano (Tóxico/Irritação)
    'rgba(153, 102, 255, 0.8)',  // Roxo (Corrosivo)
    'rgba(255, 159, 64, 0.8)',   // Laranja (Explosivo)
    'rgba(199, 199, 199, 0.8)',  // Cinza (Meio Ambiente)
    'rgba(83, 102, 255, 0.8)',   // Azul Claro (Saúde)
    'rgba(255, 0, 255, 0.8)',    // Magenta (Outros Perigos)
];

// Cores para as Bordas (apenas 100% de opacidade para destaque)
const GHS_BORDER_COLORS = [
    'rgba(255, 99, 132, 1)',
    'rgba(54, 162, 235, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
    'rgba(199, 199, 199, 1)',
    'rgba(83, 102, 255, 1)',
    'rgba(255, 0, 255, 1)',
];
// ------------------------------------

// Componente recebe os dados da API via props ({pictograma: "pictograma_nome", quantidade_produtos: 15})
const PictogramChart = ({ data }) => {
    
    // Verifica se os dados são válidos
    if (!data || data.length === 0 || (!data[0].pictograma && !data[0]._id)) {
        return <p>Sem dados de pictogramas GHS para exibir.</p>;
    }

    // 2. Transforma os dados da API para o formato do Chart.js
    const chartData = {
        // Usa 'pictograma' (novo pipeline) ou '_id' (fallback) para os rótulos
        labels: data.map(item => item.pictograma || item._id), 
        datasets: [
            {
                label: 'Quantidade de Produtos', 
                // Usa 'quantidade_produtos' (novo pipeline) ou 'count' (fallback) para os valores
                data: data.map(item => item.quantidade_produtos || item.count), 
                
                // Mapeamento Dinâmico de Cores: Usa o operador módulo (%) para ciclar pelas cores
                backgroundColor: data.map((_, index) => 
                    GHS_COLORS[index % GHS_COLORS.length]
                ),
                borderColor: data.map((_, index) => 
                    GHS_BORDER_COLORS[index % GHS_BORDER_COLORS.length]
                ),
                
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
                display: false, // Oculta a legenda, pois as cores representam apenas a barra individual
            },
            title: {
                display: true,
                text: 'Quantidade de Produtos por Pictograma GHS',
                font: {
                    size: 16
                }
            },
            tooltip: { // Melhoria opcional: Exibe apenas o valor
                callbacks: {
                    title: (context) => context[0].label,
                    label: (context) => `Quantidade: ${context.formattedValue}`
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Quantidade de Produtos' 
                },
                ticks: {
                    precision: 0 // Garante números inteiros
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Pictograma'
                },
                ticks: {
                    maxRotation: 45,
                    minRotation: 45
                }
            }
        }
    };

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default PictogramChart;