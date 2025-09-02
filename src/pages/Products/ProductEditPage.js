// src/pages/Products/ProductEditPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import productService from '../../services/productService';
import PopupMessage from '../../components/Common/PopupMessage';
import useAuth from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';

import '../../styles/productform.css';  // Você pode reutilizar ou criar um novo CSS

function ProductEditPage() {
  const { id } = useParams(); // Obtém o ID do produto da URL
  const navigate = useNavigate();
  const { user } = useAuth();

  const [product, setProduct] = useState(null); // Estado para os dados originais do produto
  const [formData, setFormData] = useState({ // Estado para os dados do formulário
    codigo: '',
    nome_do_produto: '',
    fornecedor: '',
    status: '',
    pdf_url: '', // Se o PDF puder ser alterado ou re-enviado
    // Adicione outros campos do seu produto aqui
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [messageType, setMessageType] = useState('success');

  useEffect(() => {
    const fetchProduct = async () => {
      if (!user) {
        // Se o usuário não estiver logado, PrivateRoute deve lidar com isso,
        // mas é bom ter uma verificação aqui também.
        setLoading(false);
        setError('Usuário não autenticado.');
        return;
      }

      try {
        const data = await productService.getProductById(id);
        setProduct(data); // Guarda os dados originais

        // Preenche o formulário com os dados existentes
        setFormData({
          codigo: data.codigo || '',
          nome_do_produto: data.nome_do_produto || '',
          fornecedor: data.fornecedor || '',
          status: data.status || '',
          pdf_url: data.pdf_url || '',
          // Certifique-se de preencher todos os campos que seu formulário terá
        });

        // Lógica de autorização para edição
        const canEdit = user.role === ROLES.ADMIN ||
                        (user.role === ROLES.ANALYST &&
                         data.created_by_user_id === user.id &&
                         data.status !== 'aprovado');

        if (!canEdit) {
          setError('Você não tem permissão para editar este produto.');
          setMessage('Você não tem permissão para editar este produto.');
          setMessageType('error');
          setShowMessage(true);
          // Opcional: redirecionar para a lista de produtos ou dashboard
          // setTimeout(() => navigate('/app/product-list'), 3000);
        }

        setLoading(false);
      } catch (err) {
        console.error('Erro ao buscar produto para edição:', err);
        setError('Erro ao carregar produto para edição. Verifique o ID ou suas permissões.');
        setMessage('Erro ao carregar produto: ' + (err.response?.data?.msg || 'Produto não encontrado ou erro de conexão.'));
        setMessageType('error');
        setShowMessage(true);
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id, user, navigate]); // Dependências: id do produto, user (para permissões), navigate (para redirecionar)

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Indica que a submissão está em andamento
    try {
      await productService.updateProduct(id, formData);
      setMessage('Produto atualizado com sucesso!');
      setMessageType('success');
      setShowMessage(true);
      setLoading(false);
      // Redireciona para a lista de produtos após um pequeno atraso
      setTimeout(() => navigate('/app/product-list'), 1500);
    } catch (err) {
      console.error('Erro ao atualizar produto:', err);
      setMessage('Erro ao atualizar produto: ' + (err.response?.data?.msg || 'Verifique os dados e tente novamente.'));
      setMessageType('error');
      setShowMessage(true);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="product-edit-page">
        <h1>Editar Produto</h1>
        <p>Carregando dados do produto...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-edit-page error-message">
        <h1>Editar Produto</h1>
        <p>{error}</p>
        {showMessage && (
          <PopupMessage
            message={message}
            onClose={() => setShowMessage(false)}
            type={messageType}
          />
        )}
      </div>
    );
  }

  // Se o produto não for encontrado ou não houver permissão após o carregamento
  if (!product) {
    return (
      <div className="product-edit-page">
        <h1>Editar Produto</h1>
        <p>Produto não encontrado ou você não tem permissão para visualizá-lo.</p>
        {showMessage && (
          <PopupMessage
            message={message}
            onClose={() => setShowMessage(false)}
            type={messageType}
          />
        )}
      </div>
    );
  }

  return (
    <div className="product-edit-page">
      <h1>Editar Produto</h1>
      <p>Altere as informações do produto.</p>

      <form onSubmit={handleSubmit} className="product-form">
        <div className="form-group">
          <label htmlFor="codigo">Código:</label>
          <input
            type="text"
            id="codigo"
            name="codigo"
            value={formData.codigo}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="nome_do_produto">Nome do Produto:</label>
          <input
            type="text"
            id="nome_do_produto"
            name="nome_do_produto"
            value={formData.nome_do_produto}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="fornecedor">Fornecedor:</label>
          <input
            type="text"
            id="fornecedor"
            name="fornecedor"
            value={formData.fornecedor}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="status">Status:</label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
            required
            // Opcional: Desabilitar se o usuário não for ADMIN
            disabled={user && user.role !== ROLES.ADMIN}
          >
            <option value="">Selecione o Status</option>
            <option value="pendente">Pendente</option>
            <option value="aprovado">Aprovado</option>
            <option value="rejeitado">Rejeitado</option>
          </select>
        </div>

        {/* Campo para PDF URL - ajuste conforme sua lógica de upload/atualização de PDF */}
        <div className="form-group">
          <label htmlFor="pdf_url">URL do FISPQ (PDF):</label>
          <input
            type="text"
            id="pdf_url"
            name="pdf_url"
            value={formData.pdf_url}
            onChange={handleChange}
            placeholder="URL do PDF"
          />
          {formData.pdf_url && (
            <p><a href={formData.pdf_url} target="_blank" rel="noopener noreferrer">Ver PDF Atual</a></p>
          )}
          {/* Se você tiver um sistema de re-upload de PDF, ele seria implementado aqui */}
        </div>

        <div className="form-actions">
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? 'Salvando...' : 'Salvar Alterações'}
          </button>
          <button
            type="button"
            className="cancel-button"
            onClick={() => navigate('/app/product-list')}
            disabled={loading}
          >
            Cancelar
          </button>
        </div>
      </form>

      {showMessage && (
        <PopupMessage
          message={message}
          onClose={() => setShowMessage(false)}
          type={messageType}
        />
      )}
    </div>
  );
}

export default ProductEditPage;