import { apiClient } from './api';
import { Invoice } from '../types';
import { localStore } from './store';

export const invoiceService = {
  async getInvoices(query?: string, status?: string): Promise<Invoice[]> {
    try {
      const res = await apiClient.get('/invoices', {
        params: { search: query, status },
      });
      const data = res.data;
      const items = Array.isArray(data) ? data : (data?.items || []);
      if (items && items.length > 0) return items;
      return localStore.getInvoices();
    } catch {
      let list = localStore.getInvoices();
      if (query) {
        const q = query.toLowerCase();
        list = list.filter(
          (inv) =>
            inv.invoice_number.toLowerCase().includes(q) ||
            inv.customer?.name.toLowerCase().includes(q) ||
            inv.customer?.email.toLowerCase().includes(q)
        );
      }
      if (status && status !== 'all') {
        list = list.filter((inv) => inv.status === status);
      }
      return list;
    }
  },

  async getInvoiceById(id: string): Promise<Invoice | null> {
    try {
      const res = await apiClient.get(`/invoices/${id}`);
      return res.data;
    } catch {
      return localStore.getInvoices().find((inv) => inv.id === id) || null;
    }
  },

  async updateInvoiceStatus(id: string, status: Invoice['status']): Promise<Invoice> {
    try {
      const res = await apiClient.patch(`/invoices/${id}/status`, { status });
      return res.data;
    } catch {
      const list = localStore.getInvoices().map((inv) => {
        if (inv.id === id) {
          const isPaid = status === 'paid';
          return {
            ...inv,
            status,
            paid_amount: isPaid ? inv.total_amount : inv.paid_amount,
            balance_due: isPaid ? 0 : inv.total_amount - inv.paid_amount,
          };
        }
        return inv;
      });
      localStore.setInvoices(list);
      const updated = list.find((i) => i.id === id);
      if (!updated) throw new Error('Invoice not found');
      return updated;
    }
  },
};
