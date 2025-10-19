// src/pages/Auth/LoginPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Importação dos ícones (É necessário ter o 'react-icons' instalado)
import { FaEye, FaEyeSlash } from 'react-icons/fa'; 

// Importações de hooks, serviços e componentes
import useAuth from '../../hooks/useAuth'; 
import authService from '../../services/authService'; 
import PopupMessage from '../../components/Common/PopupMessage'; 
import '../../styles/forms.css'; // Estilos do formulário

function LoginPage() {
  const navigate = useNavigate(); 
  const { user, login } = useAuth(); 
  
  // Estados para o formulário de login
  const [email, setEmail] = useState(''); 
  const [senha, setSenha] = useState(''); 
  
  // ESTADO CRÍTICO: Controla a visibilidade da senha (Inicia como false = oculto)
  const [showPassword, setShowPassword] = useState(false); 
  
  // Estados para feedback e mensagens
  const [message, setMessage] = useState(''); 
  const [showMessage, setShowMessage] = useState(false); 

  // Efeito para redirecionar o usuário se já estiver logado
  useEffect(() => {
    if (user) { 
      navigate('/app/dashboard'); 
    }
  }, [user, navigate]); 
  
  // Função para alternar o estado de visualização da senha
  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  // Função para lidar com o envio do formulário de login
  const handleSubmit = async (event) => {
    event.preventDefault(); 
    setMessage(''); 
    setShowMessage(false); 

    try {
      const data = await authService.login(email, senha); 
      login(data.access_token, data.user); 
    } catch (error) {
      console.error('Erro de login:', error); 
      const errorMessage = error.response?.data?.msg || 'Ocorreu um erro. Tente novamente mais tarde.';
      setMessage(errorMessage); 
      setShowMessage(true); 
    }
  };

  return (
    <div className="form-container">
      <h1>Acesso ao QUIMIDOCS</h1>
      <form onSubmit={handleSubmit}>
        
        {/* Input Group para Email: Garante padronização com a Senha */}
        <div className="input-group">
            <label htmlFor="email">Email:</label> 
            <input 
                type="email" 
                id="email" 
                name="email" 
                placeholder="Email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
            />
        </div>
        
        {/* Input Group para Senha */}
        <div className="input-group">
            <label htmlFor="senha">Senha:</label> 
            
            {/* Wrapper para o Input e o Ícone (position: relative no CSS) */}
            <div className="password-wrapper"> 
                <input 
                    // TIPO CONDICIONAL: 'password' (se oculto) ou 'text' (se visível)
                    type={showPassword ? 'text' : 'password'} 
                    id="senha" 
                    name="senha" 
                    placeholder="Senha" 
                    value={senha} 
                    onChange={(e) => setSenha(e.target.value)} 
                    required 
                />
                
                {/* BOTÃO/ÍCONE de toggle */}
                <button 
                    type="button" 
                    onClick={togglePasswordVisibility} 
                    className="password-toggle-icon" // Classe para posicionamento e centralização
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                    {/* Renderização condicional do ícone (FaEyeSlash = Olho fechado, FaEye = Olho aberto) */}
                    {showPassword ? <FaEye /> : <FaEyeSlash />} 
                </button>
            </div>
        </div>
        
        <button type="submit">Entrar</button>
      </form>
      
      {/* Componente de mensagem pop-up não-bloqueante */}
      {showMessage && (
        <PopupMessage 
          message={message} 
          onClose={() => setShowMessage(false)} 
          type={message.includes('sucesso') ? 'success' : 'error'} 
        />
      )}
    </div>
  );
}

export default LoginPage;