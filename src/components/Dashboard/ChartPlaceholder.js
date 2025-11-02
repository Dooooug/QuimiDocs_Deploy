// src/components/ChartPlaceholder.js
import React from 'react';

// Um componente simples para visualizar os dados que virão da API
const ChartPlaceholder = ({ title, data }) => {
    // Exemplo de transformação de dados para um formato mais comum em libs de gráfico
    const chartData = data.map(item => ({
        name: item._id, // O _id é o status ou role
        value: item.count // A contagem
    }));

    return (
        <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
            <h3>{title}</h3>
            <p>Dados para o Gráfico de {title}:</p>
            {/* Aqui você usaria sua biblioteca de gráficos (ex: <BarChart data={chartData} />) */}
            <pre style={{ backgroundColor: '#eee', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(chartData, null, 2)}
            </pre>
            <p>Total de itens: **{chartData.reduce((sum, item) => sum + item.value, 0)}**</p>
        </div>
    );
};

export default ChartPlaceholder;