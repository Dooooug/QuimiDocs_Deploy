// src/components/Dashboard/StorageByCompanyChart.js

import React, { useMemo } from 'react';
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

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

// Cores fixas para os estados físicos
const STATE_COLORS = {
    'LÍQUIDO': 'rgba(54, 162, 235, 0.8)', // Azul
    'GASOSO': 'rgba(255, 159, 64, 0.8)', // Laranja
    'SÓLIDO': 'rgba(75, 192, 192, 0.8)', // Verde/Ciano
    'PASTOSO': 'rgba(201, 203, 207, 0.8)', // Cinza
};

const StorageByCompanyChart = ({ data }) => {

    // Processamento de dados complexo usando useMemo para otimização
    const { chartData, options } = useMemo(() => {
        if (!data || data.length === 0) {
            return { chartData: null, options: {} };
        }

        // 1. Coleta todas as empresas únicas (Eixo X)
        // A nova estrutura já traz uma empresa por item no array de dados
        const companies = data.map(item => item.empresa); 

        // 2. Coleta todos os estados físicos únicos (Datasets)
        // Itera sobre todos os dados para encontrar todos os estados existentes
        const allStates = new Set();
        data.forEach(companyData => {
            companyData.dados_por_estado.forEach(stateData => {
                allStates.add(stateData.estado_fisico);
            });
        });
        const states = Array.from(allStates).sort();

        // 3. Prepara os datasets (um para cada estado físico)
        const datasets = states.map(state => {
            // Cria um array de dados, mapeando a quantidade desse 'state' para cada 'company'
            const dataForState = companies.map(companyName => {
                const companyItem = data.find(d => d.empresa === companyName);
                
                if (companyItem && companyItem.dados_por_estado) {
                    const stateItem = companyItem.dados_por_estado.find(s => s.estado_fisico === state);
                    // Retorna a quantidade ou 0 se o estado não existir para aquela empresa
                    return stateItem ? stateItem.quantidade : 0;
                }
                return 0;
            });

            // Lógica para cor
            const stateKey = state ? state.toUpperCase() : 'OUTROS';
            const color = STATE_COLORS[stateKey] || STATE_COLORS['OUTROS'];
            // Cor da borda com opacidade 1 (sólida)
            const borderColor = color.replace(/, 0\.\d+\)/, ', 1)'); 

            return {
                label: state || 'Não Definido',
                data: dataForState,
                backgroundColor: color,
                borderColor: borderColor,
                borderWidth: 1,
            };
        });
        
        // 4. Estrutura final do Chart.js
        const finalChartData = {
            labels: companies, // Rótulos do eixo X (Empresas)
            datasets: datasets, // Datasets para cada estado
        };

        // 5. Opções do gráfico (Adicionado Título)
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }, // Legenda na parte inferior
                title: { // Adicionado Título do Gráfico
                    display: true,
                    text: 'Quantidade Armazenada por Empresa e Estado Físico',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            // Retorna o rótulo do estado e a quantidade
                            return `${context.dataset.label}: ${context.parsed.y} (unidades)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: false, // Desempilhado (barras agrupadas)
                    title: { display: true, text: 'Empresa' }
                },
                y: {
                    stacked: false,
                    beginAtZero: true,
                    title: { display: true, text: 'Quantidade Armazenada (unidades)' },
                    ticks: { precision: 0 }
                }
            }
        };

        return { chartData: finalChartData, options: chartOptions };
    }, [data]);

    if (!data || data.length === 0 || !chartData) {
        return <p>Sem dados de armazenamento por empresa e estado físico.</p>;
    }

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default StorageByCompanyChart;