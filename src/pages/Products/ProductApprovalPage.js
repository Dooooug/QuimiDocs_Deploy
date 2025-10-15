// src/pages/Products/ProductApprovalPage.js

// Importações de bibliotecas e componentes essenciais do React e da aplicação.
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom'; // Hook para navegação entre páginas.
import productService from '../../services/productService'; // Service para interagir com a API de produtos.
import PopupMessage from '../../components/Common/PopupMessage'; // Componente para exibir mensagens de feedback.
import useAuth from '../../hooks/useAuth'; // Hook customizado para obter informações do usuário logado.
import { ROLES } from '../../utils/constants'; // Constantes com as roles (perfis) de usuário.
import downloadservice from '../../services/downloadservice';

// Importação da folha de estilos específica para esta página.
import '../../styles/productapproval.css';

// Definição do componente funcional da página de aprovação de produtos.
const ProductApprovalPage = () => {
  // Hook para permitir a navegação programática.
  const navigate = useNavigate();
  // Extrai as informações do usuário do hook de autenticação.
  const { user } = useAuth();
  
  // --- Estados do Componente ---
  // Estado para armazenar a lista de produtos com status 'pendente'.
  const [pendingProducts, setPendingProducts] = useState([]);
  // Estado para a mensagem de feedback a ser exibida no PopupMessage.
  const [message, setMessage] = useState('');
  // Estado para controlar a visibilidade do PopupMessage.
  const [showMessage, setShowMessage] = useState(false);
  // Estado para controlar a exibição de um indicador de carregamento.
  const [loading, setLoading] = useState(true);

  // --- Efeitos (Lifecycle) ---
  // useEffect para verificar a permissão do usuário assim que o componente é montado.
  useEffect(() => {
    // Se o usuário não estiver logado ou não for um ADMIN...
    if (!user || user.role !== ROLES.ADMIN) {
      // Define uma mensagem de acesso negado.
      setMessage('Acesso negado: Somente administradores podem aprovar produtos.');
      setShowMessage(true);
      // Redireciona o usuário para o dashboard após 3 segundos.
      setTimeout(() => {
        navigate('/app/dashboard');
      }, 3000);
    }
  }, [user, navigate]); // Dependências: Roda novamente se 'user' ou 'navigate' mudarem.

  // --- Funções ---
  // Função para buscar os produtos pendentes na API.
  // useCallback é usado para memorizar a função e evitar recriações desnecessárias.
  const fetchPendingProducts = useCallback(async () => {
    setLoading(true); // Inicia o indicador de carregamento.
    setMessage('');
    setShowMessage(false);
    try {
      // Chama o service para buscar produtos com o status 'pendente'.
      const rawProducts = await productService.getProducts('pendente');

      // Processa os produtos recebidos para garantir que cada um tenha um 'id' único e no formato string.
      // Isso previne erros de renderização caso a API retorne 'id' ou '_id' inconsistentes.
      const processed = (rawProducts || []).map((p) => {
        const safeId = String(p.id || p._id || `temp-${Math.random().toString(36).substring(2, 9)}`);
        return { ...p, id: safeId };
      });
      setPendingProducts(processed); // Atualiza o estado com a lista de produtos.
    } catch (error) {
      // Em caso de erro na busca...
      console.error('Erro ao buscar produtos pendentes:', error);
      const errorMessage = error?.response?.data?.msg || 'Erro ao carregar produtos para aprovação.';
      setMessage(errorMessage); // Define uma mensagem de erro.
      setShowMessage(true);
    } finally {
      // Este bloco é executado sempre, tanto em caso de sucesso quanto de erro.
      setLoading(false); // Para o indicador de carregamento.
    }
  }, []); // Dependências vazias: a função nunca será recriada.

  // useEffect que chama a função de busca de produtos quando o componente é montado.
  useEffect(() => {
    // A busca só é realizada se o usuário estiver logado e for um ADMIN.
    if (user && user.role === ROLES.ADMIN) {
      fetchPendingProducts();
    }
  }, [user, fetchPendingProducts]); // Dependências: Roda se 'user' ou a função 'fetchPendingProducts' mudarem.

  // Função para lidar com a aprovação ou rejeição de um produto.
  const handleUpdateStatus = async (productId, status) => {
    setMessage('');
    setShowMessage(false);

    // Validação para garantir que o ID do produto é válido.
    if (!productId) {
      setMessage('ID do produto inválido. Não foi possível prosseguir com a atualização.');
      setShowMessage(true);
      return;
    }

    try {
      // Chama o service para atualizar o status do produto na API.
      const response = await productService.updateProductStatus(productId, status);
      setMessage(response?.msg || `Produto ${productId} ${status} com sucesso!`);
      setShowMessage(true);

      // Atualiza a lista de produtos na tela, removendo o que acabou de ser processado.
      // Isso dá um feedback visual imediato para o usuário sem precisar recarregar a página.
      setPendingProducts((prev) => prev.filter((p) => p.id !== productId));
    } catch (error) {
      // Em caso de erro na atualização...
      console.error(`Erro ao ${status} produto:`, error);
      const errorMessage = error?.response?.data?.msg || `Erro ao ${status} produto. Por favor, tente novamente.`;
      setMessage(errorMessage);
      setShowMessage(true);
    }
  };

  // --- Renderização ---
  // Renderização condicional enquanto as permissões são validadas.
  if (!user || user.role !== ROLES.ADMIN) {
    return (
      <div className="product-approval-page">
        <h2>Aprovação de Produtos</h2>
        <p>{message || 'Carregando permissões...'}</p>
        {showMessage && (
          <PopupMessage message={message} onClose={() => setShowMessage(false)} type={'error'} />
        )}
      </div>
    );
  }

  // Renderização principal do componente.
  return (
    <div className="product-approval-page">
      <h2>Aprovação de Produtos</h2>
      {/* Exibe mensagem de carregamento enquanto os dados são buscados */}
      {loading ? (
        <p>Carregando produtos pendentes...</p>
      // Exibe mensagem se não houver produtos pendentes após o carregamento
      ) : pendingProducts.length === 0 ? (
        <p>Não há produtos pendentes para aprovação.</p>
      // Renderiza a lista de produtos se houver algum
      ) : (
        <div className="product-list">
          {/* Mapeia a lista de produtos para renderizar um card para cada um */}
          {pendingProducts.map((product) => (
            <div key={product.id} className="product-card-approval">
              <h3>{product.nome_do_produto} ({product.codigo})</h3>
              <p><strong>Fornecedor:</strong> {product.fornecedor}</p>
              <p><strong>Empresa:</strong> {product.empresa}</p>
              <p><strong>Quantidade:</strong> {product.quantidade_armazenada}</p>
              <p><strong>Unidade de Embalagem:</strong> {product.unidade_embalagem}</p>
              <p><strong>Estado Físico:</strong> {product.estado_fisico}</p>
              <p><strong>Local de Armazenamento:</strong> {product.local_de_armazenamento}</p>
              <p><strong>Data de Criação:</strong> {new Date(product.created_at).toLocaleDateString()}</p>
              <p><strong>Criado por:</strong> {product.created_by || product.created_by_user_id}</p>
              
             
              {/* ================================================================= */}
              {/* BLOCO DE VISUALIZAÇÃO E DOWNLOAD DO PDF (CORRIGIDO)               */}
              {/* ================================================================= */}
              {product.pdf_url && (
                <div className="pdf-actions">
                  <span>FDS:</span>
                  {/* Botão para VISUALIZAR o PDF */}
                  <button 
                    onClick={() => downloadservice.viewPdf(product.id)}
                    className="pdf-button view"
                  >
                    Visualizar
                  </button>
                  {/* Botão para FAZER O DOWNLOAD do PDF */}
                  <button 
                    onClick={() => downloadservice.downloadPdf(product.id, `${product.codigo || 'documento'}.pdf`)}
                    className="pdf-button download"
                  >
                    Download
                  </button>
                </div>
              )}
              
              {/* Botões de ação para aprovar ou rejeitar o produto */}
              <div className="approval-actions">
                <button
                  className="approve-button"
                  onClick={() => handleUpdateStatus(product.id, 'aprovado')}
                >
                  Aprovar
                </button>
                <button
                  className="reject-button"
                  onClick={() => handleUpdateStatus(product.id, 'rejeitado')}
                >
                  Rejeitar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Renderiza o componente de popup para exibir mensagens de feedback */}
      {showMessage && (
        <PopupMessage
          message={message}
          onClose={() => setShowMessage(false)}
          type={message.includes('sucesso') || message.includes('atualizado') ? 'success' : 'error'}
        />
      )}
    </div>
  );
};

export default ProductApprovalPage;