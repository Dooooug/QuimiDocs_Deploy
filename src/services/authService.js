// src/services/authService.js
import api from './api'; // Importa a instância do Axios configurada

const authService = {
  // Função para realizar o login
  // ALTERADO: de 'password' para 'senha' no parâmetro e no payload
  login: async (email, senha) => { // Login agora usa 'email' e 'senha'
    try {
      // Faz uma requisição POST para o endpoint /login da API Flask
      const response = await api.post('/login', { email, senha }); // Envia 'email' e 'senha'
      // Retorna os dados da resposta (incluindo o token JWT e informações do usuário)
      return response.data;
    } catch (error) {
      // Lança o erro para que ele possa ser tratado no componente que chamou esta função
      throw error;
    }
  },

  // Função para realizar o registro
  // ALTERADO: Agora aceita um objeto 'userData' contendo todos os campos
  register: async (userData) => { // Recebe um objeto com todos os dados do usuário
    try {
      // Faz uma requisição POST para o endpoint /register da API Flask
      // A API Flask agora espera um objeto com todos os dados (nome_do_usuario, email, senha, nivel, etc.)
      const response = await api.post('/register', userData); // Envia o objeto userData completo
      // Retorna os dados da resposta
      return response.data;
    } catch (error) {
      // Lança o erro para que ele possa ser tratado no componente
      throw error;
    }
  },
};

export default authService; // Exporta o serviço de autenticação