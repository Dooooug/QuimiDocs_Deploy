// src/pages/Products/ProductApprovalPage.js
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import productService from '../../services/productService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';

import '../../styles/productapproval.css';

const ProductApprovalPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [pendingProducts, setPendingProducts] = useState([]);
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || user.role !== ROLES.ADMIN) {
      setMessage('Acesso negado: Somente administradores podem aprovar produtos.');
      setShowMessage(true);
      setTimeout(() => {
        navigate('/app/dashboard');
      }, 3000);
    }
  }, [user, navigate]);

  const fetchPendingProducts = useCallback(async () => {
    setLoading(true);
    setMessage('');
    setShowMessage(false);
    try {
      const rawProducts = await productService.getProducts('pendente');

      const processed = (rawProducts || []).map((p) => {
        const safeId = String(p.id || p._id || `temp-${Math.random().toString(36).substring(2, 9)}`);
        return { ...p, id: safeId };
      });
      setPendingProducts(processed);
    } catch (error) {
      console.error('Erro ao buscar produtos pendentes:', error);
      const errorMessage = error?.response?.data?.msg || 'Erro ao carregar produtos para aprovação.';
      setMessage(errorMessage);
      setShowMessage(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user && user.role === ROLES.ADMIN) {
      fetchPendingProducts();
    }
  }, [user, fetchPendingProducts]);

  const handleUpdateStatus = async (productId, status) => {
    setMessage('');
    setShowMessage(false);

    if (!productId) {
      setMessage('ID do produto inválido. Não foi possível prosseguir com a atualização.');
      setShowMessage(true);
      return;
    }

    try {
      const response = await productService.updateProductStatus(productId, status);
      setMessage(response?.msg || `Produto ${productId} ${status} com sucesso!`);
      setShowMessage(true);

      setPendingProducts((prev) => prev.filter((p) => p.id !== productId));
    } catch (error) {
      console.error(`Erro ao ${status} produto:`, error);
      const errorMessage = error?.response?.data?.msg || `Erro ao ${status} produto. Por favor, tente novamente.`;
      setMessage(errorMessage);
      setShowMessage(true);
    }
  };

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

  return (
    <div className="product-approval-page">
      <h2>Aprovação de Produtos</h2>
      {loading ? (
        <p>Carregando produtos pendentes...</p>
      ) : pendingProducts.length === 0 ? (
        <p>Não há produtos pendentes para aprovação.</p>
      ) : (
        <div className="product-list">
          {pendingProducts.map((product) => (
            <div key={product.id} className="product-card-approval">
              <h3>{product.nome_do_produto} ({product.codigo})</h3>
              <p>Fornecedor: {product.fornecedor}</p>
              <p>Estado Físico: {product.estado_fisico}</p>
              <p>Criado por: {product.created_by || product.created_by_user_id}</p>
              {product.pdf_url && (
                <p>FISPQ: <a href={product.pdf_url} target="_blank" rel="noopener noreferrer">Visualizar</a></p>
              )}
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
