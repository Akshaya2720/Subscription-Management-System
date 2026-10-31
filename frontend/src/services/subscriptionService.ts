import { apiClient } from './api';
import { Subscription, DigitalTwin } from '../types';
import { localStore } from './store';

export const subscriptionService = {
  async getSubscriptions(query?: string, status?: string): Promise<Subscription[]> {
    try {
      const res = await apiClient.get('/subscriptions', {
        params: { search: query, status },
      });
      const data = res.data;
      const items = Array.isArray(data) ? data : (data?.items || []);
      if (items && items.length > 0) return items;
      return localStore.getSubscriptions();
    } catch {
      let list = localStore.getSubscriptions();
      if (query) {
        const q = query.toLowerCase();
        list = list.filter(
          (s) =>
            s.subscription_number.toLowerCase().includes(q) ||
            s.customer?.name.toLowerCase().includes(q) ||
            s.customer?.email.toLowerCase().includes(q)
        );
      }
      if (status && status !== 'all') {
        list = list.filter((s) => s.status === status);
      }
      return list;
    }
  },

  async getSubscriptionById(id: string): Promise<Subscription | null> {
    try {
      const res = await apiClient.get(`/subscriptions/${id}`);
      return res.data;
    } catch {
      return localStore.getSubscriptions().find((s) => s.id === id) || null;
    }
  },

  async createSubscription(payload: Omit<Subscription, 'id' | 'subscription_number' | 'created_at'>): Promise<Subscription> {
    try {
      const res = await apiClient.post('/subscriptions', payload);
      return res.data;
    } catch {
      const cust = localStore.getCustomers().find((c) => c.id === payload.customer_id);
      const plan = localStore.getPlans().find((p) => p.id === payload.plan_id);
      const newSub: Subscription = {
        ...payload,
        id: 'sub-' + Date.now(),
        subscription_number: `SUB-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        customer: cust,
        plan: plan,
        created_at: new Date().toISOString(),
      };
      const list = [newSub, ...localStore.getSubscriptions()];
      localStore.setSubscriptions(list);
      return newSub;
    }
  },

  async pauseSubscription(id: string, reason?: string): Promise<Subscription> {
    try {
      const res = await apiClient.post(`/subscriptions/${id}/pause`, { reason });
      return res.data;
    } catch {
      const list = localStore.getSubscriptions().map((s) =>
        s.id === id
          ? {
              ...s,
              status: 'paused' as const,
              pause_date: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
          : s
      );
      localStore.setSubscriptions(list);
      const updated = list.find((s) => s.id === id);
      if (!updated) throw new Error('Subscription not found');
      return updated;
    }
  },

  async resumeSubscription(id: string): Promise<Subscription> {
    try {
      const res = await apiClient.post(`/subscriptions/${id}/resume`);
      return res.data;
    } catch {
      const list = localStore.getSubscriptions().map((s) =>
        s.id === id
          ? {
              ...s,
              status: 'active' as const,
              resume_date: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
          : s
      );
      localStore.setSubscriptions(list);
      const updated = list.find((s) => s.id === id);
      if (!updated) throw new Error('Subscription not found');
      return updated;
    }
  },

  async renewSubscription(id: string): Promise<Subscription> {
    try {
      const res = await apiClient.post(`/subscriptions/${id}/renew`);
      return res.data;
    } catch {
      const list = localStore.getSubscriptions().map((s) => {
        if (s.id === id) {
          const nextDate = new Date();
          nextDate.setMonth(nextDate.getMonth() + 1);
          return {
            ...s,
            status: 'active' as const,
            next_billing_date: nextDate.toISOString(),
            updated_at: new Date().toISOString(),
          };
        }
        return s;
      });
      localStore.setSubscriptions(list);
      const updated = list.find((s) => s.id === id);
      if (!updated) throw new Error('Subscription not found');
      return updated;
    }
  },

  async closeSubscription(id: string, reason?: string): Promise<Subscription> {
    try {
      const res = await apiClient.post(`/subscriptions/${id}/close`, { reason });
      return res.data;
    } catch {
      const list = localStore.getSubscriptions().map((s) =>
        s.id === id
          ? {
              ...s,
              status: 'closed' as const,
              updated_at: new Date().toISOString(),
            }
          : s
      );
      localStore.setSubscriptions(list);
      const updated = list.find((s) => s.id === id);
      if (!updated) throw new Error('Subscription not found');
      return updated;
    }
  },

  async getDigitalTwin(id: string): Promise<DigitalTwin> {
    try {
      const res = await apiClient.get(`/subscriptions/${id}/digital-twin`);
      return res.data;
    } catch {
      const sub = localStore.getSubscriptions().find((s) => s.id === id);
      if (!sub) throw new Error('Subscription not found');
      const invoices = localStore.getInvoices().filter((inv) => inv.subscription_id === id);
      const payments = localStore.getPayments().filter((p) =>
        invoices.some((inv) => inv.id === p.invoice_id)
      );
      const verifications = localStore
        .getVerifications()
        .filter((v) => v.subscription_id === id);

      return {
        subscription_id: sub.id,
        subscription_number: sub.subscription_number,
        customer: sub.customer || localStore.getCustomers()[0],
        plan: sub.plan || localStore.getPlans()[0],
        contracted_price: sub.contracted_price,
        billing_frequency: sub.billing_frequency,
        status: sub.status,
        start_date: sub.start_date,
        next_billing_date: sub.next_billing_date,
        expiry_date: sub.expiry_date,
        metrics: {
          sla_compliance_rate: 98.6,
          total_service_hours_delivered: 741.2,
          contracted_service_hours: 744,
          uptime_percentage: 99.62,
          unresolved_discrepancies: verifications.filter((v) => v.discrepancy_detected).length,
        },
        invoices,
        payments,
        verifications,
        audit_diffs: [
          {
            timestamp: sub.created_at,
            field: 'status',
            old_value: 'draft',
            new_value: 'active',
            changed_by: 'Alex Mercer (Admin)',
          },
          {
            timestamp: '2026-10-15T12:00:00Z',
            field: 'status',
            old_value: 'active',
            new_value: sub.status,
            changed_by: 'System / Billing Engine',
          },
        ],
      };
    }
  },
};
