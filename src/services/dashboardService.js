// src/services/dashboardService.js

/**
 * Importa a instância central do Axios (api.js).
 * Esta instância já deve estar configurada com a baseURL (ex: '/api')
 * e os interceptors para enviar o token JWT automaticamente,
 * assim como vimos no productService.js.
 */
import api from './api';

// Criamos o objeto que conterá todos os métodos do serviço
const dashboardService = {
  
  /**
   * Busca as estatísticas agregadas do dashboard.
   * Esta função chama a rota GET /api/dashboard/stats
   * que criamos no backend.
   */
  getDashboardStats: async () => {
    try {
      /**
       * Faz a chamada GET.
       * Se sua baseURL no 'api.js' for '/api', o caminho correto é '/dashboard/stats'.
       * Se sua baseURL for apenas '/', o caminho seria '/api/dashboard/stats'.
       * * Baseado no seu productService.js (que chama '/products'), 
       * vou assumir que a baseURL é '/api' e o prefixo do blueprint
       * é '/dashboard', como na instrução anterior.
       */
      const response = await api.get('/dashboard/stats');
      
      // Retorna apenas os dados da resposta (o objeto JSON com as estatísticas)
      return response.data;

    } catch (error) {
      // Se a API retornar um erro (ex: 401, 403, 500),
      // o 'api.js' (Axios) irá lançar uma exceção.
      // Nós a "relançamos" (throw) para que o componente (DashboardPage.js) 
      // possa capturá-la e exibir uma mensagem de erro.
      throw error;
    }
  },
  
  // No futuro, se você tiver mais rotas no dashboard (ex: /api/dashboard/charts),
  // você pode adicionar as funções aqui.
  
};

// Exporta o serviço para ser usado em outros lugares (como na DashboardPage)
export default dashboardService;