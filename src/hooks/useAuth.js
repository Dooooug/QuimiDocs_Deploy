// src/hooks/useAuth.js
import { useContext } from 'react';
import { AuthContext } from '../context/authContext'; // Ajuste o caminho

// Hook personalizado para consumir o AuthContext
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

export default useAuth;
