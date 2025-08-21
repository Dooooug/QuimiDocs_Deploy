// src/App.js
import React from 'react';
import Navbar from './components/common/Navbar';
import AppRoutes from './routes/AppRoutes'; // assumindo que você já tem o AppRoutes configurado

function App() {
  return (
    <div className="App">
      {/* Navbar global */}
      <Navbar />

      {/* Conteúdo das rotas */}
      <div className="content">
        <AppRoutes />
      </div>
    </div>
  );
}

export default App;
