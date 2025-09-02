// src/pages/Auth/RegisterPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../../services/authService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth'; // Importa useAuth para pegar o token
import { ROLES } from '../../utils/constants'; // Importa ROLES para o select

import '../../styles/forms.css';

function RegisterPage() {
  const [formData, setFormData] = useState({
    nome_do_usuario: '',
    email: '',
    senha: '',
    nivel: ROLES.VIEWER, // Valor padrão
    cpf: '',
    empresa: '',
    setor: '',
    data_de_nascimento: '', // Formato DD/MM/AAAA
    planta: '',
  });
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth(); // Pega o usuário logado para verificar a role

  // Redireciona se não for ADMIN (proteção adicional no frontend)
  React.useEffect(() => {
    if (user && user.role !== ROLES.ADMIN) {
      setMessage('Acesso negado: Somente administradores podem registrar novos usuários.');
      setShowMessage(true);
      setTimeout(() => {
        navigate('/app/dashboard');
      }, 3000);
    } else if (!user) { // Se não estiver logado
      setMessage('Você precisa estar logado como administrador para acessar esta página.');
      setShowMessage(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    }
  }, [user, navigate]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleDateChange = (e) => {
    let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não for dígito

    if (value.length > 8) {
      value = value.substring(0, 8); // Limita a 8 dígitos (DDMMYYYY)
    }

    // Adiciona as barras automaticamente
    if (value.length > 2 && value.length <= 4) {
      value = `${value.substring(0, 2)}/${value.substring(2)}`;
    } else if (value.length > 4) {
      value = `${value.substring(0, 2)}/${value.substring(2, 4)}/${value.substring(4, 8)}`;
    }

    setFormData({ ...formData, data_de_nascimento: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setShowMessage(false);

    try {
      const response = await authService.register(formData);
      setMessage(response.msg);
      setShowMessage(true);
      // Limpa o formulário após o sucesso ou redireciona
      setFormData({
        nome_do_usuario: '',
        email: '',
        senha: '',
        nivel: ROLES.VIEWER,
        cpf: '',
        empresa: '',
        setor: '',
        data_de_nascimento: '',
        planta: '',
      });
      setTimeout(() => {
        navigate('/app/users'); // Redireciona para a lista de usuários após o registro
      }, 2000);
    } catch (error) {
      console.error('Erro de registro:', error);
      const errorMessage = error.response?.data?.msg || 'Erro ao registrar usuário.';
      setMessage(errorMessage);
      setShowMessage(true);
    }
  };

  // Função para voltar para a página de gerenciamento de usuários
  const handleGoBack = () => {
    navigate('/app/users');
  };

  // Se o usuário não for ADMIN e não estiver logado, exibe mensagem e redireciona
  if (!user || user.role !== ROLES.ADMIN) {
    return (
      <div className="register-container">
        {showMessage && (
          <PopupMessage
            message={message}
            onClose={() => setShowMessage(false)}
            type={'error'}
          />
        )}
        <h2 style={{color: '#f44336'}}>Acesso Restrito</h2>
        <p>Você não tem permissão para registrar novos usuários.</p>
        {/* Botão para voltar adicionado aqui também para caso de acesso negado */}
        <button type="button" className="back-button" onClick={handleGoBack}>Voltar</button>
      </div>
    );
  }

  return (
    <div className="register-container">
      <h2>Registrar Novo Usuário</h2>
      <form onSubmit={handleSubmit}>
        {/* Todos os campos do formulário */}
        <div className="form-group">
          <label htmlFor="nome_do_usuario">Nome do Usuário:</label>
          <input
            type="text"
            id="nome_do_usuario"
            name="nome_do_usuario"
            value={formData.nome_do_usuario}
            onChange={handleInputChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="senha">Senha:</label>
          <input
            type="password"
            id="senha"
            name="senha"
            value={formData.senha}
            onChange={handleInputChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="nivel">Nível:</label>
          <select
            id="nivel"
            name="nivel"
            value={formData.nivel}
            onChange={handleInputChange}
            required
          >
            {/* Mapeia os ROLES para opções do select */}
            {Object.values(ROLES).map(role => (
              <option key={role} value={role}>{role.charAt(0).toUpperCase() + role.slice(1)}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="cpf">CPF:</label>
          <input
            type="text"
            id="cpf"
            name="cpf"
            value={formData.cpf}
            onChange={handleInputChange}
            maxLength="14" // Max length for CPF (111.222.333-44)
            placeholder="Ex: 123.456.789-00"
          />
        </div>
        <div className="form-group">
          <label htmlFor="empresa">Empresa:</label>
          <input
            type="text"
            id="empresa"
            name="empresa"
            value={formData.empresa}
            onChange={handleInputChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="setor">Setor:</label>
          <input
            type="text"
            id="setor"
            name="setor"
            value={formData.setor}
            onChange={handleInputChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="data_de_nascimento">Data de Nascimento (DD/MM/AAAA):</label>
          <input
            type="text"
            id="data_de_nascimento"
            name="data_de_nascimento"
            value={formData.data_de_nascimento}
            onChange={handleDateChange} // Usa a nova função de formatação
            placeholder="DD/MM/AAAA"
            maxLength="10"
          />
        </div>
        <div className="form-group">
          <label htmlFor="planta">Planta:</label>
          <input
            type="text"
            id="planta"
            name="planta"
            value={formData.planta}
            onChange={handleInputChange}
          />
        </div>

        {/* O container dos botões foi movido para o final do formulário */}
        <div className="form-buttons-container">
          <button type="button" className="back-button" onClick={handleGoBack}>Voltar</button>
          <button type="submit" className="submit-button">Registrar</button>
        </div>
      </form>
      {showMessage && (
        <PopupMessage
          message={message}
          onClose={() => setShowMessage(false)}
          type={message.includes('sucesso') ? 'success' : 'error'}
          duration={3000}
        />
      )}
    </div>
  );
}

export default RegisterPage;