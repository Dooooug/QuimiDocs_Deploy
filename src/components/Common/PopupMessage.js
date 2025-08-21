// src/components/Common/PopupMessage.js
import React from 'react';
import '../../styles/popup.css'; // Crie este arquivo CSS para estilizar o popup

function PopupMessage({ message, type = 'info', onClose }) {
  // O useEffect que configurava o temporizador foi removido.
  // O popup agora permanecerá na tela até que o usuário o feche.

  return (
    <div className="popup-overlay">
        <div className={`popup-message ${type}`} role="alert" aria-live="assertive">
        <p>{message}</p>
        <button className="popup-close-button" onClick={onClose}>&times;</button>
        </div>
    </div>
  );
}

export default PopupMessage;