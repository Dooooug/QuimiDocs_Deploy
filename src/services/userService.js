// src/services/userService.js
import api from './api';          // já configura baseURL e interceptor do token

const userService = {
  /** Lista todos os usuários (ADMIN) */
  getAllUsers: async () => {
    const { data } = await api.get('/users');
    return data;                 // => array de usuários
  },

  /** Atualiza um usuário pelo ID */
  updateUser: async (id, payload) => {
    const { data } = await api.put(`/users/${id}`, payload);
    return data;                 // => usuário atualizado
  },

  /** Deleta um usuário pelo ID */
  deleteUser: async (id) => {
    const { data } = await api.delete(`/users/${id}`);
    return data;                 // => { msg: 'Usuário deletado com sucesso' }
  },
};

export default userService;
