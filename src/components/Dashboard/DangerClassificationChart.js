// src/components/Dashboard/DangerClassificationChart.js

import React from 'react';
// 💥 MUDANÇA: Importa elementos para o gráfico de Barras/Colunas
import { 
    Chart as ChartJS, 
    CategoryScale, // Eixo X
    LinearScale,   // Eixo Y
    BarElement,    // Elemento da Barra
    Title, 
    Tooltip, 
    Legend 
} from 'chart.js';
// 💥 MUDANÇA: Importa o componente Bar
import { Bar } from 'react-chartjs-2'; 

// 1. Registra os elementos necessários
// 💥 MUDANÇA: Registra os componentes de Bar/Coluna
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

// Cores personalizadas mapeadas para a ordem dos tipos de perigo no pipeline:
// Ordem do Pipeline: 1. Físico, 2. À Saúde, 3. Ao Meio Ambiente
const DANGER_CLASSIFICATION_COLORS = [
    'rgba(54, 162, 235, 0.8)',   // Azul/Ciano claro (Físico)
    'rgba(255, 99, 132, 0.8)',   // Vermelho (À Saúde)
    'rgba(75, 192, 192, 0.8)',   // Verde/Ciano (Ao Meio Ambiente)
];

// Componente recebe os dados da API via props ({tipo: "classificacao", quantidade: 50})
const DangerClassificationChart = ({ data }) => {
    
    // 2. Transforma os dados da API para o formato do Chart.js
    const chartData = {
        labels: data.map(item => item.tipo), 
        datasets: [
            {
                // 💥 MUDANÇA: A legenda é útil em gráfico de coluna para indicar o que as barras representam
                label: 'Quantidade de Produtos', 
                data: data.map(item => item.quantidade), 
                
                // As cores dinâmicas permanecem, mapeando para cada coluna
                backgroundColor: DANGER_CLASSIFICATION_COLORS.slice(0, data.length),
                borderColor: DANGER_CLASSIFICATION_COLORS.slice(0, data.length).map(color => color.replace('0.8', '1')), 
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
                // 💥 MUDANÇA: Legenda agora fica em cima
                position: 'top', 
                display: false, // Ocultamos, pois cada barra tem sua cor única e a legenda é redundante
            },
            title: {
                display: true, 
                text: 'Classificação por Tipo de Perigo',
                font: { size: 16 }
            },
            tooltip: {
                callbacks: {
                    // 💥 MUDANÇA: Simplificamos o tooltip, removendo o cálculo de porcentagem (melhor para coluna)
                    label: (context) => `Produtos: ${context.formattedValue}`,
                }
            },
        },
        // 💥 NOVO/MUDANÇA: Configurações de Eixos X e Y
        scales: {
            x: {
                title: { 
                    display: true, 
                    text: 'Tipo de Perigo' 
                },
            },
            y: {
                beginAtZero: true,
                title: { 
                    display: true, 
                    text: 'Quantidade de Produtos' 
                },
                ticks: { 
                    precision: 0 // Garante que os valores do eixo Y sejam números inteiros
                }
            }
        }
    };

    if (!data || data.length === 0) {
        return <p>Sem dados de classificação de perigo para exibir.</p>;
    }

    return (
        // 💥 MUDANÇA: Renderiza o componente Bar
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} /> 
        </div>
    );
};

export default DangerClassificationChart;