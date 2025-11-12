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
// O plugin de Data Labels foi REMOVIDO para simplificar o estilo
import { Bar } from 'react-chartjs-2';

// Registra APENAS os componentes padrão necessários do Chart.js
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
    'SÓLIDO': 'rgba(75, 192, 192, 0.8)', // Verde/Ciano
    'GASOSO': 'rgba(255, 159, 64, 0.8)', // Laranja
    'PASTOSO': 'rgba(201, 203, 207, 0.8)', // Cinza
};

// =========================================================================
// NOVO: DADOS SIMULADOS PARA TESTE E DESENVOLVIMENTO
// Os valores fornecidos por você estão aqui.
// =========================================================================
const DADOS_SIMULADOS_PADRAO = [
    {
        "empresa": "EMPRESA A",
        "dados_por_estado": [
            { "estado_fisico": "LÍQUIDO", "quantidade": 10 },
            { "estado_fisico": "GASOSO", "quantidade": 20 },
            { "estado_fisico": "SÓLIDO", "quantidade": 30 },
            { "estado_fisico": "PASTOSO", "quantidade": 35 }
        ]
    },
    {
        "empresa": "EMPRESA B",
        "dados_por_estado": [
            { "estado_fisico": "LÍQUIDO", "quantidade": 10 },
            { "estado_fisico": "GASOSO", "quantidade": 20 },
            { "estado_fisico": "SÓLIDO", "quantidade": 30 },
            { "estado_fisico": "PASTOSO", "quantidade": 35 }
        ]
    },
    {
        "empresa": "EMPRESA C",
        "dados_por_estado": [
            { "estado_fisico": "LÍQUIDO", "quantidade": 10 },
            { "estado_fisico": "GASOSO", "quantidade": 20 },
            { "estado_fisico": "SÓLIDO", "quantidade": 30 },
            { "estado_fisico": "PASTOSO", "quantidade": 35 }
        ]
    }
];


/**
 * Componente de Gráfico de Armazenamento por Empresa e Estado Físico.
 * * @param {Array<Object>} data - Os dados de 'storage_by_company_and_state' 
 * (agrupados por empresa e estado) passados pelo DashboardPage.
 */
const StorageByCompanyChart = ({ data }) => { 

    // ----------------------------------------------------------------------
    // MUDANÇA PRINCIPAL: Define a fonte de dados, priorizando a prop 'data'.
    // Se a prop estiver vazia ou não for fornecida, usa os dados simulados.
    // ----------------------------------------------------------------------
    const dataToProcess = (data && data.length > 0) ? data : DADOS_SIMULADOS_PADRAO;


    // Processamento de dados complexo usando useMemo para otimização
    // O useMemo agora usa 'dataToProcess' como a fonte e dependência.
    const { chartData, options } = useMemo(() => {
        
        // Retorna um estado vazio se os dados forem nulos, vazios ou indefinidos
        if (!dataToProcess || dataToProcess.length === 0) {
            return { chartData: null, options: {} };
        }

        // 1. Coleta todas as empresas únicas (Eixo X)
        const companies = dataToProcess.map(item => item.empresa); 

        // 2. Coleta todos os estados físicos únicos (Datasets)
        const allStates = new Set();
        dataToProcess.forEach(companyData => {
            companyData.dados_por_estado.forEach(stateData => {
                // Mantenha a normalização para MAIÚSCULAS para robustez
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
                const companyItem = dataToProcess.find(d => d.empresa === companyName);
                
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

        // 5. Opções do gráfico (Com melhorias de visualização)
        const chartOptions = {
             responsive: true,
             maintainAspectRatio: false,
             plugins: {
                 // POSIÇÃO DA LEGENDA ALTERADA PARA 'top'
                 legend: { position: 'top' }, 
                 // TÍTULO DO GRÁFICO PRINCIPAL DESATIVADO
                 title: { 
                     display: false,
                 },
                 tooltip: {
                     callbacks: {
                         label: function(context) {
                             // Formata a quantidade no tooltip (ex: remove decimais desnecessários)
                             const quantity = Number.isInteger(context.parsed.y) ? context.parsed.y : context.parsed.y.toFixed(2);
                             return `${context.dataset.label}: ${quantity} (unidades)`;
                         }
                     }
                 },
                 // CONFIGURAÇÃO DE DATALABELS REMOVIDA
             },
             scales: {
                 x: {
                     stacked: true, // Barras Empilhadas (Mantido)
                     title: { display: true, text: 'Empresa' },
                     // ROTAÇÃO DE TICKS REMOVIDA
                 },
                 y: {
                     stacked: true, // Barras Empilhadas (Mantido)
                     beginAtZero: true,
                     title: { display: true, text: 'Quantidade Armazenada (unidades)' },
                     ticks: { precision: 0 } 
                 }
             }
         };

        return { chartData: finalChartData, options: chartOptions };
    }, [dataToProcess]); // MUDANÇA: A dependência agora é 'dataToProcess'

    // Mensagem de dados vazios
    // MUDANÇA: Verifica dataToProcess
    if (!dataToProcess || dataToProcess.length === 0 || !chartData) {
        // Se o componente pai gerenciar o carregamento, esta mensagem aparecerá após o carregamento
        return <p>Sem dados de armazenamento por empresa e estado físico.</p>;
    }

    // A altura deve ser gerenciada pelo componente pai ou pelo style externo
    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
};

export default StorageByCompanyChart;