// src/services/productService.js
import api from './api';

const productService = {
  // Esta função continua útil se você precisar criar um produto sem FDS em outro lugar
  createProduct: async (productData) => {
    try {
      const response = await api.post('/products', productData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // ALTERAÇÃO: Adicionar esta nova função
  createProductWithPdf: async (formData) => {
    try {
      // A rota é a principal '/products', que agora sabe lidar com FormData.
      // Não definimos headers aqui, o navegador faz isso por nós.
      const response = await api.post('/products', formData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getProducts: async (statusFilter = null) => {
    try {
      const url = statusFilter
        ? `/products?status=${encodeURIComponent(statusFilter)}`
        : '/products';
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getProductById: async (productId) => {
    try {
      const response = await api.get(`/products/${productId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateProduct: async (productId, updatedData) => {
    try {
      const response = await api.put(`/products/${productId}`, updatedData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  deleteProduct: async (productId) => {
    try {
      const response = await api.delete(`/products/${productId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateProductStatus: async (productId, status) => {
    try {
      const response = await api.put(`/products/${productId}/status`, { status });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getNextProductCode: async () => {
    try {
      const response = await api.get('/products/next-code');
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

export default productService;