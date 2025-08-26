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
  const [uploadedFileName, setUploadedFileName] = useState(null);

  if (!show) {
    return null;
  }

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setUploadedFileName(null);
  };

  const handleUpload = async () => {
    // Lógica de upload...
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

    if (selectedFile.type !== 'application/pdf') {
      setUploadMessage('O arquivo deve estar no formato PDF.');
      setShowUploadMessage(true);
      return;
    }

    const fileNameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, "").toLowerCase().trim();
    const productNameNormalized = productNameForFispq.toLowerCase().trim();

    if (fileNameWithoutExt !== productNameNormalized) {
      setUploadMessage(`O nome do arquivo deve ser exatamente igual ao nome do produto: "${productNameForFispq}".`);
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
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      onUploadComplete(res.data.url, res.data.s3_file_key);

      setUploadMessage('FDS anexado com sucesso!');
      setShowUploadMessage(true);
      setUploadedFileName(selectedFile.name);
      setSelectedFile(null);

    } catch (error) {
      console.error('Erro ao enviar FDS:', error);
      const errorMessage = error.response?.data?.error || 'Erro ao anexar FDS.';
      setUploadMessage(errorMessage);
      setShowUploadMessage(true);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div className="popup-overlay">
        <div className="popup-message">
          <button onClick={onClose} className="popup-close-button">
            &times;
          </button>
          
          <h3>Anexar FDS para o Produto: {productNameForFispq || productId}</h3>

          <input type="file" accept="application/pdf" onChange={handleFileChange} />

          <button onClick={handleUpload} disabled={uploading}>
            {uploading ? 'Enviando...' : 'Anexar'}
          </button>

          {uploadedFileName && (
            <p style={{ marginTop: '10px', color: 'green' }}>
              ✅ Arquivo anexado: <strong>{uploadedFileName}</strong>
            </p>
          )}

        </div>
      </div>
      {showUploadMessage && (
        <PopupMessage
          message={uploadMessage}
          onClose={() => setShowUploadMessage(false)}
          type={uploadMessage.includes('sucesso') ? 'success' : 'error'}
        />
      )}
    </>
  );
}

export default UploadForm;