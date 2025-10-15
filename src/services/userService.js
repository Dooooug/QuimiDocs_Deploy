import api from './api';          // já configura baseURL e interceptor do token

const userService = {
  /** Lista todos os usuários (ADMIN) */
  getAllUsers: async () => {
    const { data } = await api.get('/users');
    return data;                 // => array de usuários
  },

  /** Atualiza um usuário pelo ID */
  updateUser: async (id, payload) => {
    const { data } = await api.put(`/users/${id}`, payload);
    return data;                 // => usuário atualizado
  },

  /** Deleta um usuário pelo ID */
  deleteUser: async (id) => {
    const { data } = await api.delete(`/users/${id}`);
    return data;                 // => { msg: 'Usuário deletado com sucesso' }
  },

  // ✅ NOVO: Função para registrar um novo usuário
  /**
   * Registra um novo usuário.
   * @param {object} userData - Dados do novo usuário (username, email, password, etc.)
   * @returns {Promise<object>} - A resposta da API com os dados do usuário criado.
   */
  registerUser: async (userData) => {
    // A rota /register é pública, então não precisa de token.
    const { data } = await api.post('/register', userData);
    return data;
  },
};

export default userService;