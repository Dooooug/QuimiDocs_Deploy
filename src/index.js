// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import AppRoutes from './routes/AppRoutes'; // Importe seu AppRoutes
import './styles/global.css'; // Crie este arquivo para estilos globais/reset
// import './index.css'; // Opcional, pode ser mesclado com global.css

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AppRoutes /> {/* Renderize seu componente de rotas principal */}
  </React.StrictMode>
);

