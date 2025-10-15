// src/pages/Users/UserManagement.js
// Página de gerenciamento de usuários – apenas para administradores
// Exibe lista, permite editar em modal e excluir com confirmação.

import React, { useState, useEffect, useCallback } from "react";

import useAuth from "../../hooks/useAuth";
import userService from "../../services/userService";

import PopupMessage from "../../components/Common/PopupMessage";
import UserEditModal from "../../components/UserEditModal";
import ConfirmationModal from "../../components/ConfirmationModal";

import { ROLES } from "../../utils/constants";

import "../../styles/UserManagement.css";
import "../../styles/Modal.css";

/**
 * Componente que permite ao ADMIN visualizar, editar e excluir usuários.
 * Segurança: redireciona não-logados ou usuários sem permissão.
 */
const UserManagement = () => {
  const { user, token } = useAuth();
 

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [toast, setToast] = useState({ show: false, message: "", type: "success" });

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);

  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  /** Busca usuários no backend */
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!token) throw new Error("Token de autenticação não encontrado.");
      const data = await userService.getAllUsers(); // <— sem token no parâmetro
      setUsers(data);
    } catch (err) {
      const msg = err.response?.data?.msg || "Erro ao carregar usuários.";
      setError(msg);
      setToast({ show: true, message: msg, type: "error" });
    } finally {
      setLoading(false);
    }
  }, [token]);

  /** Verifica permissões e carrega dados */
  useEffect(() => {
    if (!user || !token) return; // espera AuthContext hidratar
    if (user.role !== ROLES.ADMIN) {
      setToast({ show: true, message: "Acesso negado.", type: "error" });
      return;
    }
    fetchUsers();
  }, [user, token, fetchUsers]);

  /* —— Handlers ————————————————————————— */
  const openEditModal = (u) => {
    setEditingUser(u);
    setIsEditModalOpen(true);
  };

  const openRegisterModal = () => {
    setIsRegisterModalOpen(true);
  };

  const openDeleteModal = (u) => {
    setUserToDelete(u);
    setIsConfirmModalOpen(true);
  };

  const handleDelete = async () => {
    if (!userToDelete) return;
    console.log('ID do usuário a ser deletado (frontend):', userToDelete.id);
    console.log('Tipo do ID (frontend):', typeof userToDelete.id);
    try {
      await userService.deleteUser(userToDelete.id); // <— sem token
      setToast({ show: true, message: "Usuário deletado com sucesso!", type: "success" });
      await fetchUsers();
    } catch (err) {
      const msg = err.response?.data?.msg || "Erro ao deletar usuário.";
      setToast({ show: true, message: msg, type: "error" });
    } finally {
      setIsConfirmModalOpen(false);
      setUserToDelete(null);
    }
  };

  const handleSave = async (updatedUser) => {
    try {
      await userService.updateUser(updatedUser.id, updatedUser); // <— sem token
      setToast({ show: true, message: "Usuário atualizado com sucesso!", type: "success" });
      setIsEditModalOpen(false);
      setEditingUser(null);
      await fetchUsers();
    } catch (err) {
      const msg = err.response?.data?.msg || "Erro ao atualizar usuário.";
      setToast({ show: true, message: msg, type: "error" });
    }
  };

  const handleRegister = async (newUserData) => {
    try {
      await userService.registerUser(newUserData);
      setToast({ show: true, message: "Usuário registrado com sucesso!", type: "success" });
      setIsRegisterModalOpen(false); // Fecha o modal de registro
      await fetchUsers(); // Atualiza a lista de usuários na tela
    } catch (err) {
      const msg = err.response?.data?.msg || "Erro ao registrar usuário.";
      setToast({ show: true, message: msg, type: "error" });
    }
  };



  /* —— Render ————————————————————————— */
  if (loading) return <div className="user-management-container"><p>Carregando...</p></div>;
  if (error) return (
    <div className="user-management-container">
      <h2 style={{ color: "#f44336" }}>Erro</h2>
      <p>{error}</p>
    </div>
  );

  return (
    <div className="user-management-container">
      <h2>Gerenciar Usúarios</h2>
      
       <button className="register-user-button" onClick={openRegisterModal}>
        Registrar Novo Usuário
      </button>
      <table className="user-table">
        <thead>
          <tr>
            <th>Data de Criação</th>
            <th>Nome de Usuário</th>
            <th>Email</th>
            <th>Nível</th>
            <th>CPF</th>
            <th>Empresa</th>
            <th>Setor</th>
            <th>Data de Nascimento</th>
            <th>Planta</th>
            <th>Último Acesso</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {users.length ? (
            users.map((u) => (
              <tr key={u.id}>
                <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                <td>{u.username}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.cpf || "—"}</td>
                <td>{u.empresa || "—"}</td>
                <td>{u.setor || "—"}</td>
                <td>{u.data_de_nascimento || "—"}</td>
                <td>{u.planta || "—"}</td>
                <td>{u.last_access ? new Date(u.last_access).toLocaleString() : 'Nunca'}</td>
                <td>
                  <button className="action-button edit-button" onClick={() => openEditModal(u)}>Editar</button>
                  <button className="action-button delete-button" onClick={() => openDeleteModal(u)}>Deletar</button>
                </td>
              </tr>
            ))
        ) : (
          <tr>
            <td colSpan="11">Nenhum usuário encontrado.</td>
          </tr>
        )}
      </tbody>
      </table>

      {/* —— Modais —— */}
      {isEditModalOpen && (
        <UserEditModal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} user={editingUser} onSave={handleSave} />
      )}
      {isRegisterModalOpen && (
        <UserEditModal
          isOpen={isRegisterModalOpen}
          onClose={() => setIsRegisterModalOpen(false)}
          onSave={handleRegister}
          // Não passamos a prop 'user', para o modal saber que está em modo de criação
        />
      )}
      {isConfirmModalOpen && (
        <ConfirmationModal isOpen={isConfirmModalOpen} onClose={() => setIsConfirmModalOpen(false)} onConfirm={handleDelete} message={`Tem certeza que deseja excluir o usuário ${userToDelete?.username}? Essa ação é irreversível.`} />
      )}

      {toast.show && (
        <PopupMessage message={toast.message} onClose={() => setToast({ ...toast, show: false })} type={toast.type} duration={3000} />
      )}
    </div>
  );
};

export default UserManagement;
