// src/services/downloadService.js
import api from './api'; // ⚙️ Axios configurado com JWT no header Authorization

const downloadService = {
  /**
   * 🔐 Obtém do back-end um link temporário (presigned URL)
   * para download/visualização do arquivo PDF no S3.
   * O back-end valida o JWT e só então retorna a URL.
   *
   * @param {string} productId - ID do produto no banco
   * @returns {Promise<string>} - URL temporária (válida por poucos minutos)
   */
  getDownloadUrl: async (productId) => {
    try {
      // ✅ O Axios já envia o JWT automaticamente no header
      const response = await api.get(`/products/${productId}/download`);

      // 🔍 Valida se o back-end realmente retornou o campo esperado
      if (!response.data || !response.data.download_url) {
        throw new Error('O servidor não retornou o link de download.');
      }

      return response.data.download_url;
    } catch (error) {
      console.error('❌ Erro ao obter link temporário do PDF:', error);
      throw error;
    }
  },

  /**
   * 👁️ Visualiza o PDF em nova aba do navegador.
   * O arquivo é carregado diretamente do S3 via presigned URL.
   *
   * @param {string} productId - ID do produto
   */
  viewPdf: async (productId) => {
    try {
      const url = await downloadService.getDownloadUrl(productId);

      // 🔗 Abre em nova aba, visualização inline do PDF
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('❌ Erro ao abrir PDF:', error);
      alert('Não foi possível abrir o PDF. Tente novamente.');
    }
  },

  /**
   * 💾 Força o download do PDF localmente, sem abrir no navegador.
   *
   * @param {string} productId - ID do produto
   * @param {string} filename - Nome sugerido para o arquivo
   */
  downloadPdf: async (productId, filename = 'arquivo.pdf') => {
    try {
      const url = await downloadService.getDownloadUrl(productId);

      // 📎 Cria um link temporário e dispara o download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;

      // 🔒 Evita problemas com CSP e sandbox de browsers
      link.target = '_blank';
      link.rel = 'noopener noreferrer';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('❌ Erro ao baixar PDF:', error);
      alert('Não foi possível baixar o PDF. Tente novamente.');
    }
  },
};

export default downloadService;

