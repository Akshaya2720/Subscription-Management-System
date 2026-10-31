import { apiClient } from './api';
import { Product, Plan } from '../types';
import { localStore } from './store';

export const productService = {
  async getProducts(): Promise<Product[]> {
    try {
      const res = await apiClient.get('/products');
      return res.data;
    } catch {
      return localStore.getProducts();
    }
  },

  async createProduct(payload: Omit<Product, 'id' | 'created_at'>): Promise<Product> {
    try {
      const res = await apiClient.post('/products', payload);
      return res.data;
    } catch {
      const newProduct: Product = {
        ...payload,
        id: 'prod-' + Date.now(),
        created_at: new Date().toISOString(),
      };
      const list = [newProduct, ...localStore.getProducts()];
      localStore.setProducts(list);
      return newProduct;
    }
  },

  async updateProduct(id: string, payload: Partial<Product>): Promise<Product> {
    try {
      const res = await apiClient.put(`/products/${id}`, payload);
      return res.data;
    } catch {
      const list = localStore.getProducts().map((p) =>
        p.id === id ? { ...p, ...payload, updated_at: new Date().toISOString() } : p
      );
      localStore.setProducts(list);
      const updated = list.find((p) => p.id === id);
      if (!updated) throw new Error('Product not found');
      return updated;
    }
  },

  async toggleProductStatus(id: string): Promise<Product> {
    try {
      const res = await apiClient.patch(`/products/${id}/status`);
      return res.data;
    } catch {
      const list = localStore.getProducts().map((p) =>
        p.id === id ? { ...p, is_active: !p.is_active } : p
      );
      localStore.setProducts(list);
      const updated = list.find((p) => p.id === id);
      if (!updated) throw new Error('Product not found');
      return updated;
    }
  },

  async getPlans(): Promise<Plan[]> {
    try {
      const res = await apiClient.get('/plans');
      return res.data;
    } catch {
      return localStore.getPlans();
    }
  },

  async createPlan(payload: Omit<Plan, 'id' | 'created_at'>): Promise<Plan> {
    try {
      const res = await apiClient.post('/plans', payload);
      return res.data;
    } catch {
      const newPlan: Plan = {
        ...payload,
        id: 'plan-' + Date.now(),
        created_at: new Date().toISOString(),
      };
      const list = [newPlan, ...localStore.getPlans()];
      localStore.setPlans(list);
      return newPlan;
    }
  },

  async updatePlan(id: string, payload: Partial<Plan>): Promise<Plan> {
    try {
      const res = await apiClient.put(`/plans/${id}`, payload);
      return res.data;
    } catch {
      const list = localStore.getPlans().map((p) =>
        p.id === id ? { ...p, ...payload } : p
      );
      localStore.setPlans(list);
      const updated = list.find((p) => p.id === id);
      if (!updated) throw new Error('Plan not found');
      return updated;
    }
  },
};
