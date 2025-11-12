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

// Registra os componentes necessários do Chart.js
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

// Cores fixas para os estados físicos
// Mapeamento estrito baseado nos valores validados.
const STATE_COLORS = {
    'LÍQUIDO': 'rgba(54, 162, 235, 0.8)', // Azul
    'SÓLIDO': 'rgba(75, 192, 192, 0.8)', // Verde/Ciano
    'GASOSO': 'rgba(255, 159, 64, 0.8)', // Laranja
    'PASTOSO': 'rgba(201, 203, 207, 0.8)', // Cinza
};

// =========================================================================
// Dados simulados e a lógica de busca interna foram REMOVIDOS.
// O componente AGORA recebe os dados via props.
// =========================================================================

/**
 * Componente de Gráfico de Armazenamento por Empresa e Estado Físico.
 * * @param {Array<Object>} data - Os dados de 'storage_by_company_and_state'
 * passados pelo componente pai (DashboardPage).
 */
const StorageByCompanyChart = ({ data }) => { 

    // Processamento de dados complexo usando useMemo para otimização
    const { chartData, options } = useMemo(() => {
        
        // Retorna um estado vazio se os dados forem nulos, vazios ou indefinidos
        if (!data || data.length === 0) {
            return { chartData: null, options: {} };
        }

        // 1. Coleta todas as empresas únicas (Eixo X)
        const companies = data.map(item => item.empresa); 

        // 2. Coleta todos os estados físicos únicos (Datasets)
        const allStates = new Set();
        data.forEach(companyData => {
            companyData.dados_por_estado.forEach(stateData => {
                // Normaliza para letras MAIÚSCULAS para garantir agrupamento correto.
                // Esta normalização ainda é útil caso o backend não garanta UPPERCASE 
                // para todos os campos 'estado_fisico'.
                if (stateData.estado_fisico) {
                    allStates.add(stateData.estado_fisico.toUpperCase()); 
                }
            });
        });
        const states = Array.from(allStates).sort(); 

        // 3. Prepara os datasets (um para cada estado físico)
        const datasets = states.map(state => {
            
            // Mapeia a quantidade desse 'state' para cada 'company' no eixo X.
            const dataForState = companies.map(companyName => {
                const companyItem = data.find(d => d.empresa === companyName);
                
                if (companyItem && companyItem.dados_por_estado) {
                    // Normaliza o estado físico do item de dados para MAIÚSCULAS antes da comparação.
                    const stateItem = companyItem.dados_por_estado.find(s => 
                        s.estado_fisico && s.estado_fisico.toUpperCase() === state
                    );
                    
                    // Retorna a quantidade ou 0 se o estado não existir para aquela empresa
                    return stateItem ? stateItem.quantidade : 0;
                }
                return 0; 
            });

            // Lógica para cor: usa a chave em UPPERCASE para buscar a cor mapeada.
            const stateKey = state || '';
            // Se o estado não for encontrado, usa uma cor padrão neutra (cinza claro)
            const color = STATE_COLORS[stateKey] || 'rgba(220, 220, 220, 0.8)'; 
            
            // Cor da borda com opacidade 1 (sólida) para melhor contraste
            const borderColor = color.replace(/, 0\.\d+\)/, ', 1)'); 

            return {
                label: state || 'Não Definido', // Rótulo na legenda
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

        // 5. Opções do gráfico (Inalterado)
        const chartOptions = {
             responsive: true,
             maintainAspectRatio: false,
             plugins: {
                 legend: { position: 'bottom' }, 
                 title: { 
                     display: true,
                     text: 'Quantidade Armazenada por Empresa e Estado Físico',
                     font: { size: 16 }
                 },
                 tooltip: {
                     callbacks: {
                         label: function(context) {
                             // Certifica-se que a quantidade é exibida como inteiro se for o caso
                             const quantity = Number.isInteger(context.parsed.y) ? context.parsed.y : context.parsed.y.toFixed(2);
                             return `${context.dataset.label}: ${quantity} (unidades)`;
                         }
                     }
                 }
             },
             scales: {
                 x: {
                     stacked: false, // Barras AGRUPADAS
                     title: { display: true, text: 'Empresa' }
                 },
                 y: {
                     stacked: false,
                     beginAtZero: true,
                     title: { display: true, text: 'Quantidade Armazenada (unidades)' },
                     ticks: { 
                         // Permite números inteiros ou flutuantes, mas tenta formatar para precisão 0 se possível
                         precision: 0 
                     } 
                 }
             }
         };

        return { chartData: finalChartData, options: chartOptions };
    }, [data]); // Dependência: A lógica roda sempre que 'data' muda

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