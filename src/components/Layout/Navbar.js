import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';
import '../../styles/Navbar.css';
import logo from '../../assets/logo_quimidocs-trans.png';

function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [isProductsDropdownOpen, setIsProductsDropdownOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isOpen, setIsOpen] = useState(false); // controle do menu hambúrguer

  const handleNavigation = (path) => {
    if (path === '/logout') {
      logout();
    } else {
      navigate(`/app/${path}`);
    }
    setIsProductsDropdownOpen(false);
    setIsUserDropdownOpen(false);
    setIsOpen(false); // fecha o menu após navegação
  };

  const toggleProductsDropdown = () => {
    setIsProductsDropdownOpen(!isProductsDropdownOpen);
    setIsUserDropdownOpen(false);
  };

  const toggleUserDropdown = () => {
    setIsUserDropdownOpen(!isUserDropdownOpen);
    setIsProductsDropdownOpen(false);
  };

  const toggleMenu = () => setIsOpen(!isOpen); // alterna menu hambúrguer

  if (!user) return null;

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/app/dashboard" className="navbar-logo-link">
          <img src={logo} alt="Logo QUIMIDOCS" className="navbar-logo" />
        </Link>
        <span className="welcome-message-navbar">
          Seja bem vindo, {user.username}, Nível: {user.role}
        </span>

        {/* Botão hamburguer visível apenas no mobile */}
        <span className="navbar-toggle" onClick={toggleMenu}>
          ☰
        </span>
      </div>

      <ul className={`navbar-menu ${isOpen ? 'active' : ''}`}>
        <li className="navbar-item dropdown">
          <button className="dropdown-toggle" onClick={toggleProductsDropdown}>
            Produtos
          </button>
          {isProductsDropdownOpen && (
            <ul className="dropdown-menu">
              {(user.role === ROLES.ADMIN || user.role === ROLES.ANALYST) && (
                <li><button onClick={() => handleNavigation('product-registration')}>Cadastrar Produtos</button></li>
              )}
              {user.role === ROLES.ADMIN && (
                <li><button onClick={() => handleNavigation('product-approval')}>Aprovar Produtos</button></li>
              )}
              {(user.role === ROLES.ADMIN || user.role === ROLES.ANALYST || user.role === ROLES.VIEWER) && (
                <li><button onClick={() => handleNavigation('product-list')}>Lista de Produtos Cadastrados</button></li>
              )}
            </ul>
          )}
        </li>

        <li className="navbar-item">
          <button onClick={() => handleNavigation('dashboard')}>Dashboard</button>
        </li>

        <li className="navbar-item dropdown">
          <button className="dropdown-toggle" onClick={toggleUserDropdown}>
            Usuário
          </button>
          {isUserDropdownOpen && (
            <ul className="dropdown-menu">
              {user.role === ROLES.ADMIN && (
                <li><button onClick={() => handleNavigation('users')}>Gerenciar Usuários</button></li>
              )}
              <li><button onClick={() => handleNavigation('account')}>Minha Conta</button></li>
            </ul>
          )}
        </li>

        <li className="navbar-item">
          <button onClick={() => handleNavigation('/logout')}>Sair</button>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
