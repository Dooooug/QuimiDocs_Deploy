// src/context/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom'; // Manter useNavigate para outros usos futuros

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const navigate = useNavigate(); // Manter o hook, caso ele precise ser usado em outros lugares

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
        // Ao carregar a página, se já estiver logado, redireciona para o dashboard
        // Isso é útil para manter o estado de login se a página for recarregada
        // A navegação aqui também pode ser window.location.href para ser mais robusta
        // navigate('/app/dashboard'); // Pode ser um ponto de problema secundário
      } catch (e) {
        console.error("Erro ao fazer parse do usuário do localStorage:", e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', JSON.stringify(userData));
    
    console.log("DEBUG: Tentando navegar para (window.location.href):", '/app/dashboard');
    // <<-- ATENÇÃO AQUI: MUDANÇA PARA TESTE DE DIAGNÓSTICO -->>
    window.location.href = '/app/dashboard'; // Força uma navegação completa do navegador
    // Se isso funcionar, o problema está na integração do React Router ou no ambiente.
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
