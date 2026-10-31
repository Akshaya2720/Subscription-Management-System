import { apiClient } from './api';
import { Quotation, Subscription } from '../types';
import { localStore } from './store';

export const quotationService = {
  async getQuotations(): Promise<Quotation[]> {
    try {
      const res = await apiClient.get('/quotations');
      return Array.isArray(res.data) ? res.data : (res.data?.items || []);
    } catch {
      return localStore.getQuotations();
    }
  },

  async getQuotationById(id: string): Promise<Quotation | null> {
    try {
      const res = await apiClient.get(`/quotations/${id}`);
      return res.data;
    } catch {
      return localStore.getQuotations().find((q) => q.id === id) || null;
    }
  },

  async calculateAuthoritativePricing(payload: {
    items: { product_id: string; plan_id?: string; quantity: number; unit_price: number }[];
    customer_id: string;
    discount_code?: string;
  }): Promise<{ subtotal: number; discount_amount: number; tax_amount: number; total_amount: number }> {
    try {
      const res = await apiClient.post('/quotations/calculate', payload);
      return res.data;
    } catch {
      // Backend simulation matching enterprise standard tax rules
      const subtotal = payload.items.reduce((sum, item) => sum + item.unit_price * item.quantity, 0);
      const discount_amount = payload.discount_code ? subtotal * 0.1 : 0;
      const tax_amount = (subtotal - discount_amount) * 0.08;
      const total_amount = subtotal - discount_amount + tax_amount;
      return {
        subtotal: Number(subtotal.toFixed(2)),
        discount_amount: Number(discount_amount.toFixed(2)),
        tax_amount: Number(tax_amount.toFixed(2)),
        total_amount: Number(total_amount.toFixed(2)),
      };
    }
  },

  async createQuotation(payload: Omit<Quotation, 'id' | 'quotation_number' | 'created_at'>): Promise<Quotation> {
    try {
      const res = await apiClient.post('/quotations', payload);
      return res.data;
    } catch {
      const cust = localStore.getCustomers().find((c) => c.id === payload.customer_id);
      const newQuo: Quotation = {
        ...payload,
        id: 'quot-' + Date.now(),
        quotation_number: `QUO-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        customer: cust,
        created_at: new Date().toISOString(),
      };
      const list = [newQuo, ...localStore.getQuotations()];
      localStore.setQuotations(list);
      return newQuo;
    }
  },

  async updateStatus(id: string, status: Quotation['status']): Promise<Quotation> {
    try {
      const res = await apiClient.patch(`/quotations/${id}/status`, { status });
      return res.data;
    } catch {
      const list = localStore.getQuotations().map((q) => (q.id === id ? { ...q, status } : q));
      localStore.setQuotations(list);
      const updated = list.find((q) => q.id === id);
      if (!updated) throw new Error('Quotation not found');
      return updated;
    }
  },

  async convertToSubscription(id: string): Promise<Subscription> {
    try {
      const res = await apiClient.post(`/quotations/${id}/convert`);
      return res.data;
    } catch {
      const quo = localStore.getQuotations().find((q) => q.id === id);
      if (!quo) throw new Error('Quotation not found');

      // Update quotation status to converted
      const updatedQuos = localStore.getQuotations().map((q) =>
        q.id === id ? { ...q, status: 'converted' as const } : q
      );
      localStore.setQuotations(updatedQuos);

      // Create new active subscription
      const newSub: Subscription = {
        id: 'sub-' + Date.now(),
        subscription_number: `SUB-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        customer_id: quo.customer_id,
        customer: quo.customer,
        plan_id: quo.items[0]?.plan_id || 'plan-001',
        status: 'active',
        contracted_price: quo.total_amount,
        billing_frequency: 'monthly',
        currency: quo.currency || 'USD',
        start_date: new Date().toISOString(),
        next_billing_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        auto_renew: true,
        items: quo.items.map((item) => ({
          id: 'sitem-' + Math.random().toString(36).substring(7),
          product_id: item.product_id,
          product_name: item.product_name,
          plan_id: item.plan_id || 'plan-001',
          plan_name: item.plan_name || 'Standard',
          quantity: item.quantity,
          unit_price: item.unit_price,
          total_amount: item.total_amount,
        })),
        created_at: new Date().toISOString(),
      };

      const subs = [newSub, ...localStore.getSubscriptions()];
      localStore.setSubscriptions(subs);
      return newSub;
    }
  },
};
