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

    if (!productNameForFispq) {
      setUploadMessage('Nome do produto não fornecido. Não é possível anexar FDS.');
      setShowUploadMessage(true);
      return;
    }

    setUploading(true);
    setUploadMessage('');
    setShowUploadMessage(false);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('product_name', productNameForFispq);

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadMessage('FDS anexado com sucesso!');
      setShowUploadMessage(true);
      // **CORREÇÃO:** Acessa as propriedades diretamente do objeto de resposta.
      onUploadComplete(response.url, response.s3_file_key); 
      
      setSelectedFile(null);

    } catch (error) {
      console.error('Erro ao enviar FDS:', error);
      // **CORREÇÃO:** Acessa a propriedade 'error' diretamente do objeto de erro.
      const errorMessage = error.response?.error || 'Erro ao anexar FDS.';
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