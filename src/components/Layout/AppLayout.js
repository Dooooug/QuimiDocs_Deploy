// src/components/Layout/AppLayout.js
import React from 'react'; // Removido useState, pois não é mais necessário para o Navbar
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar'; // Importa o novo componente Navbar
import '../../styles/AppLayout.css';
import '../../styles/Navbar.css'; // Importa os estilos da Navbar

function AppLayout() {
  // Removido const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  // Removido const toggleSidebar = () => { ... };

  return (
    <div className="app-layout">
      {/* Removido o botão Hambúrguer, pois agora faz parte da lógica interna do Navbar, se necessário */}
      <Navbar /> {/* Renderiza o Navbar aqui */}
      <div className="content">
        <Outlet /> {/* O Outlet renderizará os componentes das rotas aninhadas aqui */}
      </div>
    </div>
  );
}

export default AppLayout;