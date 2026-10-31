import { apiClient } from './api';
import { Customer } from '../types';
import { localStore } from './store';

export const customerService = {
  async getCustomers(query?: string, status?: string): Promise<Customer[]> {
    try {
      const response = await apiClient.get('/customers', {
        params: { search: query, status },
      });
      const data = response.data;
      const items = Array.isArray(data) ? data : (data?.items || []);
      if (items && items.length > 0) return items;
      return localStore.getCustomers();
    } catch {
      let list = localStore.getCustomers();
      if (query) {
        const q = query.toLowerCase();
        list = list.filter(
          (c) =>
            c.name.toLowerCase().includes(q) ||
            c.email.toLowerCase().includes(q) ||
            (c.company_name && c.company_name.toLowerCase().includes(q))
        );
      }
      if (status && status !== 'all') {
        list = list.filter((c) => c.status === status);
      }
      return list;
    }
  },

  async getCustomerById(id: string): Promise<Customer | null> {
    try {
      const response = await apiClient.get(`/customers/${id}`);
      return response.data;
    } catch {
      const list = localStore.getCustomers();
      return list.find((c) => c.id === id) || null;
    }
  },

  async createCustomer(payload: Omit<Customer, 'id' | 'created_at'>): Promise<Customer> {
    try {
      const response = await apiClient.post('/customers', payload);
      return response.data;
    } catch {
      const newCustomer: Customer = {
        ...payload,
        id: 'cust-' + Date.now(),
        created_at: new Date().toISOString(),
        total_spend: 0,
        active_subscriptions_count: 0,
      };
      const list = [newCustomer, ...localStore.getCustomers()];
      localStore.setCustomers(list);
      return newCustomer;
    }
  },

  async updateCustomer(id: string, payload: Partial<Customer>): Promise<Customer> {
    try {
      const response = await apiClient.put(`/customers/${id}`, payload);
      return response.data;
    } catch {
      const list = localStore.getCustomers().map((c) =>
        c.id === id ? { ...c, ...payload, updated_at: new Date().toISOString() } : c
      );
      localStore.setCustomers(list);
      const updated = list.find((c) => c.id === id);
      if (!updated) throw new Error('Customer not found');
      return updated;
    }
  },

  async deleteCustomer(id: string): Promise<void> {
    try {
      await apiClient.delete(`/customers/${id}`);
    } catch {
      const list = localStore.getCustomers().filter((c) => c.id !== id);
      localStore.setCustomers(list);
    }
  },
};
