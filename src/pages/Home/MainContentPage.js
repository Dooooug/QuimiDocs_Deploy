// src/pages/Home/MainContentPage.js
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth'; // Importa o hook useAuth para acessar o contexto
import { ROLES } from '../../utils/constants'; // Importa as constantes de papel
import '../../styles/MainContentPage.css'; // Estilos do formulário de autenticação

function MainContentPage() {
  const navigate = useNavigate();
  const { user } = useAuth(); // Obtém o objeto de usuário logado do contexto

  // Este efeito redireciona usuários logados para o dashboard.
  // Se você deseja que usuários logados (admin ou não) possam ver esta página
  // para talvez acessar o botão "Registrar" para outros usuários,
  // precisará revisar a lógica de redirecionamento em AppRoutes ou aqui.
  // No entanto, para o propósito de demonstrar a restrição, vamos manter o redirecionamento.
  useEffect(() => {
    if (user) {
      navigate('/app/dashboard'); 
    }
  }, [user, navigate]);

  const handleLoginClick = () => {
    navigate('/login');
  };

  const handleRegisterClick = () => {
    navigate('/register');
  };

  // Determina se o usuário logado é um administrador
  const isAdmin = user && user.role === ROLES.ADMIN;
  // Determina se o usuário está logado, mas NÃO é um administrador
  const isLoggedNonAdmin = user && user.role !== ROLES.ADMIN;

  return (
    <div className="main-content">
      <h1>Bem-vindo ao QUIMIDOCS</h1>
      <h1>Gerenciamento Inteligente De Produtos Químicos</h1>
      <div className="button-container">
        {/* Botão de Entrar é sempre visível se o usuário NÃO estiver logado */}
        {!user && <button onClick={handleLoginClick}>Entrar</button>}

        {/* Lógica para o botão "Registrar":
          1. Se o usuário NÃO estiver logado, o botão "Registrar" é para auto-registro.
             No entanto, como o backend /register exige ADMIN, esta opção levará a um erro 403.
             Para um fluxo de auto-registro padrão, a rota /register no backend NÃO deveria ser restrita a ADMIN.
             Pense bem nesta decisão de UX/segurança. Se você quer auto-registro, remova o @role_required([ROLES['ADMIN']])
             do endpoint /register no Flask e talvez adicione validações de role no registro de outros users.
             
             Por enquanto, para atender estritamente ao "limitar para somente administrador" na visibilidade do botão,
             vamos esconder o botão "Registrar" para usuários não logados, forçando-os a logar primeiro.
             Isso torna o registro de novos usuários uma ação apenas para administradores logados (que seriam redirecionados para o dashboard).
             Se a intenção é que admins logados criem outros usuários, o ideal seria ter este botão em uma página interna.
        */}

        {/* Opção para exibir o botão "Registrar" APENAS se o usuário for ADMIN (e estiver logado) */}
        {isAdmin && (
          <button onClick={handleRegisterClick}>Registrar Novo Usuário</button>
        )}

        {/* Mensagem para usuários logados que NÃO são administradores */}
        {isLoggedNonAdmin && (
          <p className="permission-message">Você não tem permissão para registrar novos usuários.</p>
        )}

        {/*
          Alternativa: Se você quiser que o botão "Registrar" esteja sempre visível para usuários NÃO LOGADOS
          para permitir o auto-registro (e então o backend lida com a permissão):
          {!user && <button onClick={handleRegisterClick}>Registrar</button>}
          
          Nesse caso, a mensagem para não-admins logados ainda se aplicaria, mas o fluxo de auto-registro seria diferente.
          A implementação atual prioriza a restrição visual direta na MainContentPage.
        */}
      </div>
    </div>
  );
}

export default MainContentPage;
