// src/pages/Products/UploadForm.js
import React, { useState } from 'react';
import '../../styles/popup.css'; 
import api from '../../services/api'; 
import PopupMessage from '../../components/Common/PopupMessage';

function UploadForm({ productId, productNameForFispq, show, onClose, onUploadComplete }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [showUploadMessage, setShowUploadMessage] = useState(false);
  const [uploading, setUploading] = useState(false);

  if (!show) {
    return null;
  }

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadMessage('Por favor, selecione um arquivo.');
      setShowUploadMessage(true);
      return;
    }

    // ALTERAÇÃO 1: Usamos o 'productId' para a requisição.
    // Ele é mais confiável que o nome para identificar o produto no backend.
    if (!productId) {
      setUploadMessage('ID do produto não fornecido. Não é possível anexar FDS.');
      setShowUploadMessage(true);
      return;
    }

    setUploading(true);
    setUploadMessage('');
    setShowUploadMessage(false);

    const formData = new FormData();
    formData.append('file', selectedFile);
    // Não precisamos mais enviar 'product_name' no formulário, pois o ID vai na URL.
    
    try {
      // ALTERAÇÃO 2: A URL da requisição agora inclui o 'productId'.
      // Exemplo: a requisição será para "http://127.0.0.1:5000/upload/60c72b2f9b1d8c001f8e4a9e"
      const response = await api.post(`/upload/${productId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadMessage('FDS anexado com sucesso!');
      setShowUploadMessage(true);

      // ALTERAÇÃO 3: As respostas do Axios ficam dentro de 'response.data'.
      // Corrigimos o acesso à URL e à chave do arquivo.
      onUploadComplete(response.data.url, response.data.s3_file_key); 
      
      setSelectedFile(null);

    } catch (error) {
      console.error('Erro ao enviar FDS:', error);
      
      // ALTERAÇÃO 4: A mensagem de erro enviada pelo backend também está em 'error.response.data'.
      const errorMessage = error.response?.data?.error || 'Erro ao anexar FDS. Verifique sua conexão ou tente novamente.';
      setUploadMessage(errorMessage);
      setShowUploadMessage(true);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="popup-overlay">
      <div className="popup-message active" style={{ display: 'block', maxWidth: '500px', margin: 'auto', top: '50%', transform: 'translateY(-50%)' }}>
        <h3>Anexar FDS para o Produto: {productNameForFispq || productId}</h3>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? 'Enviando...' : 'Anexar'}
        </button>
        <button onClick={onClose} className="popup-close-button">&times;</button>
        {showUploadMessage && (
          <PopupMessage
            message={uploadMessage}
            onClose={() => setShowUploadMessage(false)}
            type={uploadMessage.includes('sucesso') ? 'success' : 'error'}
          />
        )}
      </div>
    </div>
  );
}

export default UploadForm;