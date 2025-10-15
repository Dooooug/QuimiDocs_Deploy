// src/components/UserEditModal.js
import React, { useState, useEffect, useCallback } from 'react';
import '../styles/Modal.css';
import { ROLES } from '../utils/constants';

// --- ETAPA 1: Adicionar os campos que faltavam ao estado inicial ---
const INITIAL_FORM_STATE = {
  nome_do_usuario: '',
  email: '',
  nivel: ROLES.USER,
  cpf: '', // <<< ADICIONADO
  empresa: '', // <<< ADICIONADO
  setor: '', // <<< ADICIONADO
  data_de_nascimento: '', // <<< ADICIONADO
  planta: '', // <<< ADICIONADO
  senha: '',
};

function UserEditModal({ user, onClose, onSave }) {
  const isEditMode = !!user;

  const getInitialData = useCallback(() => {
    if (isEditMode) {
      // --- ETAPA 2: Mapear os novos campos para o modo de edição ---
      return {
        id: user.id,
        nome_do_usuario: user.username,
        email: user.email,
        nivel: user.role,
        cpf: user.cpf || '', // <<< ADICIONADO
        empresa: user.empresa || '', // <<< ADICIONADO
        setor: user.setor || '', // <<< ADICIONADO
        data_de_nascimento: user.data_de_nascimento || '', // <<< ADICIONADO
        planta: user.planta || '', // <<< ADICIONADO
        senha: '',
      };
    }
    return INITIAL_FORM_STATE;
  }, [user, isEditMode]);

  const [formData, setFormData] = useState(getInitialData);

  useEffect(() => {
    setFormData(getInitialData());
  }, [getInitialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const dataToSend = { ...formData };
    if (!dataToSend.senha.trim()) {
      delete dataToSend.senha;
    }
    if (!isEditMode) {
      delete dataToSend.id; 
    }
    onSave(dataToSend);
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-content">
        <h3>{isEditMode ? `Editar Usuário: ${user.username}` : 'Registrar Novo Usuário'}</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="nome_do_usuario">Nome de Usuário:</label>
            <input type="text" id="nome_do_usuario" name="nome_do_usuario" value={formData.nome_do_usuario} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="email">Email:</label>
            <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="nivel">Nível:</label>
            <select id="nivel" name="nivel" value={formData.nivel} onChange={handleChange} required>
              {Object.values(ROLES).map((role) => (
                <option key={role} value={role}>{role.toUpperCase()}</option>
              ))}
            </select>
          </div>

          {/* --- ETAPA 3: Adicionar os novos campos ao formulário JSX --- */}
          <div className="form-group">
            <label htmlFor="cpf">CPF:</label>
            <input type="text" id="cpf" name="cpf" value={formData.cpf} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label htmlFor="empresa">Empresa:</label>
            <input type="text" id="empresa" name="empresa" value={formData.empresa} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label htmlFor="setor">Setor:</label>
            <input type="text" id="setor" name="setor" value={formData.setor} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label htmlFor="data_de_nascimento">Data de Nascimento:</label>
            <input type="date" id="data_de_nascimento" name="data_de_nascimento" value={formData.data_de_nascimento} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label htmlFor="planta">Planta:</label>
            <input type="text" id="planta" name="planta" value={formData.planta} onChange={handleChange} />
          </div>
          {/* --- Fim dos campos adicionados --- */}

          <div className="form-group">
            <label htmlFor="senha">Nova Senha ({isEditMode ? 'opcional' : 'obrigatório'}):</label>
            <input type="password" id="senha" name="senha" value={formData.senha} onChange={handleChange} placeholder={isEditMode ? "Deixe em branco para não alterar" : ""} required={!isEditMode} />
          </div>
          <div className="modal-actions">
            <button type="submit" className="save-btn">
              {isEditMode ? 'Salvar Alterações' : 'Registrar Usuário'}
            </button>
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserEditModal;