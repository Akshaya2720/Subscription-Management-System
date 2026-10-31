import { apiClient } from './api';
import { DashboardMetrics } from '../types';
import { localStore } from './store';
import { initialDashboardMetrics } from './fallbackData';

export const dashboardService = {
  async getMetrics(range = '30d'): Promise<DashboardMetrics> {
    try {
      const res = await apiClient.get('/dashboard/metrics', { params: { range } });
      return res.data;
    } catch {
      // Calculate dynamic metrics based on current live store records
      const customers = localStore.getCustomers();
      const subs = localStore.getSubscriptions();
      const activeSubs = subs.filter((s) => s.status === 'active');
      const invoices = localStore.getInvoices();
      const overdue = invoices.filter((i) => i.status === 'overdue');
      const payments = localStore.getPayments();

      const revenueReceived = payments.reduce((sum, p) => sum + p.amount, 0);
      const totalOutstanding = invoices.reduce((sum, i) => sum + i.balance_due, 0);

      const metrics: DashboardMetrics = {
        ...initialDashboardMetrics,
        active_subscriptions: activeSubs.length,
        total_customers: customers.length,
        revenue_received: revenueReceived > 0 ? revenueReceived : 284500,
        outstanding_amount: totalOutstanding > 0 ? totalOutstanding : 32400,
        overdue_invoices: overdue.length,
        upcoming_renewals: activeSubs.filter((s) => s.auto_renew).length,
      };

      return metrics;
    }
  },
};
