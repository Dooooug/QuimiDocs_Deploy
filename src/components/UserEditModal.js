// src/components/UserEditModal.js
import React, { useState, useEffect } from 'react';
import '../styles/Modal.css'; // Estilos gerais para modais
import { ROLES } from '../utils/constants'; // Para exibir as opções de nível

function UserEditModal({ user, onClose, onSave }) {
  const [formData, setFormData] = useState({
    id: user.id,
    nome_do_usuario: user.username, // Mapeia para o campo da API
    email: user.email,
    nivel: user.role, // Mapeia para o campo da API
    cpf: user.cpf || '',
    empresa: user.empresa || '',
    setor: user.setor || '',
    data_de_nascimento: user.data_de_nascimento || '',
    planta: user.planta || '',
    senha: '' // Senha é opcional para atualização
  });

  // Atualiza o formData se o usuário mudar (útil se o modal for reutilizado)
  useEffect(() => {
    setFormData({
      id: user.id,
      nome_do_usuario: user.username,
      email: user.email,
      nivel: user.role,
      cpf: user.cpf || '',
      empresa: user.empresa || '',
      setor: user.setor || '',
      data_de_nascimento: user.data_de_nascimento || '',
      planta: user.planta || '',
      senha: ''
    });
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Cria um objeto com os dados que realmente serão enviados para a API
    const dataToSend = { ...formData };
    if (!dataToSend.senha) {
      delete dataToSend.senha; // Não envia a senha se estiver vazia
    }
    onSave(dataToSend);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Editar Usuário: {user.username}</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="nome_do_usuario">Nome de Usuário:</label>
            <input
              type="text"
              id="nome_do_usuario"
              name="nome_do_usuario"
              value={formData.nome_do_usuario}
              onChange={handleChange}
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
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="nivel">Nível:</label>
            <select
              id="nivel"
              name="nivel"
              value={formData.nivel}
              onChange={handleChange}
              required
            >
              {Object.values(ROLES).map((role) => (
                <option key={role} value={role}>{role.toUpperCase()}</option>
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
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="empresa">Empresa:</label>
            <input
              type="text"
              id="empresa"
              name="empresa"
              value={formData.empresa}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="setor">Setor:</label>
            <input
              type="text"
              id="setor"
              name="setor"
              value={formData.setor}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="data_de_nascimento">Data de Nascimento:</label>
            <input
              type="date"
              id="data_de_nascimento"
              name="data_de_nascimento"
              value={formData.data_de_nascimento}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="planta">Planta:</label>
            <input
              type="text"
              id="planta"
              name="planta"
              value={formData.planta}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="senha">Nova Senha (opcional):</label>
            <input
              type="password"
              id="senha"
              name="senha"
              value={formData.senha}
              onChange={handleChange}
              placeholder="Deixe em branco para não alterar"
            />
          </div>
          <div className="modal-actions">
            <button type="submit" className="save-btn">Salvar</button>
            <button type="button" className="cancel-btn" onClick={onClose}>Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserEditModal;