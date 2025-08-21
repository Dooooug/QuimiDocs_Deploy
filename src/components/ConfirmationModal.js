// src/components/ConfirmationModal.js
import React from 'react';
import '../styles/Modal.css'; // Reutiliza os estilos de modal

function ConfirmationModal({ message, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay">
      <div className="modal-content small-modal">
        <h3>Confirmação</h3>
        <p>{message}</p>
        <div className="modal-actions">
          <button className="confirm-btn" onClick={onConfirm}>Confirmar</button>
          <button className="cancel-btn" onClick={onCancel}>Cancelar</button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmationModal;