// src/pages/Auth/LoginPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth'; // Hook personalizado para usar o AuthContext
import authService from '../../services/authService'; // Serviço para interagir com a API de autenticação
import PopupMessage from '../../components/Common/PopupMessage'; // Componente para exibir mensagens não-bloqueantes
import '../../styles/forms.css'; // Estilos do formulário de autenticação

function LoginPage() {
  const navigate = useNavigate(); // Hook para navegação programática
  const { user, login } = useAuth(); // Obtém o estado do usuário logado e a função de login do contexto
  
  // ALTERADO: 'username' para 'email' para refletir o login por email no backend
  const [email, setEmail] = useState(''); 
  // ALTERADO: 'password' para 'senha' para padronizar com o backend
  const [senha, setSenha] = useState(''); 
  
  const [message, setMessage] = useState(''); // Estado para armazenar mensagens de feedback
  const [showMessage, setShowMessage] = useState(false); // Estado para controlar a visibilidade do PopupMessage

  // Efeito para redirecionar o usuário para o dashboard se já estiver logado
  useEffect(() => {
    if (user) { 
      navigate('/app/dashboard'); // Redireciona para o dashboard se já houver um usuário logado
    }
  }, [user, navigate]); // Dependências do efeito: 'user' e 'navigate'

  // Função para lidar com o envio do formulário de login
  const handleSubmit = async (event) => {
    event.preventDefault(); // Previne o comportamento padrão de recarregar a página
    setMessage(''); // Limpa mensagens anteriores
    setShowMessage(false); // Esconde qualquer mensagem de feedback anterior

    try {
      // ALTERADO: Chama o serviço de login com 'email' e 'senha'
      const data = await authService.login(email, senha); 
      
      // Se o login for bem-sucedido, chama a função 'login' do contexto
      // passando o token de acesso e os dados do usuário (que incluem o ID e a role)
      login(data.access_token, data.user); 
      // O redirecionamento para o dashboard é feito dentro da função 'login' do AuthContext
    } catch (error) {
      console.error('Erro de login:', error); // Loga o erro completo no console para depuração
      // Lida com diferentes tipos de erro na resposta da API, priorizando a mensagem do backend
      const errorMessage = error.response?.data?.msg || 'Ocorreu um erro. Tente novamente mais tarde.';
      setMessage(errorMessage); // Define a mensagem de erro a ser exibida
      setShowMessage(true); // Exibe o PopupMessage
    }
  };



  return (
    <div className="form-container">
      <h1>Acesso ao QUIMIDOCS</h1>
      <form onSubmit={handleSubmit}>
        {/* Campo de entrada para o Email */}
        <label htmlFor="email">Email:</label> {/* Label adicionado para acessibilidade */}
        <input 
          type="email" // Tipo "email" para validação de formato
          id="email" // ID para associar ao label
          name="email" // Nome do campo
          placeholder="Email" 
          value={email} // Valor controlado pelo estado 'email'
          onChange={(e) => setEmail(e.target.value)} // Atualiza o estado ao digitar
          required // Campo obrigatório
        />
        
        {/* Campo de entrada para a Senha */}
        <label htmlFor="senha">Senha:</label> {/* Label adicionado para acessibilidade */}
        <input 
          type="password" // Tipo "password" para ocultar a entrada
          id="senha" // ID para associar ao label
          name="senha" // Nome do campo
          placeholder="Senha" 
          value={senha} // Valor controlado pelo estado 'senha'
          onChange={(e) => setSenha(e.target.value)} // Atualiza o estado ao digitar
          required // Campo obrigatório
        />
        <button type="submit">Entrar</button>
      </form>
      
      
      
      {/* Componente de mensagem pop-up não-bloqueante, visível se showMessage for true */}
      {showMessage && (
        <PopupMessage 
          message={message} 
          onClose={() => setShowMessage(false)} 
          type={message.includes('sucesso') ? 'success' : 'error'} // Define o tipo da mensagem (cor)
        />
      )}
    </div>
  );
}

export default LoginPage;
