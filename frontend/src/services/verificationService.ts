import { apiClient } from './api';
import { VerificationContract } from '../types';
import { localStore } from './store';

export const verificationService = {
  async getVerifications(): Promise<VerificationContract[]> {
    try {
      const res = await apiClient.get('/verification/contracts');
      const data = res.data;
      const items = Array.isArray(data) ? data : (data?.items || []);
      if (items && items.length > 0) return items;
      return localStore.getVerifications();
    } catch {
      return localStore.getVerifications();
    }
  },

  async approveCredit(id: string, notes?: string): Promise<VerificationContract> {
    try {
      const res = await apiClient.post(`/verification/contracts/${id}/approve`, { notes });
      return res.data;
    } catch {
      const list = localStore.getVerifications().map((v) =>
        v.id === id
          ? {
              ...v,
              status: 'approved' as const,
              approved_by: 'Alex Mercer (Platform Admin)',
              approved_at: new Date().toISOString(),
            }
          : v
      );
      localStore.setVerifications(list);
      const updated = list.find((v) => v.id === id);
      if (!updated) throw new Error('Contract verification not found');
      return updated;
    }
  },

  async rejectCredit(id: string, reason?: string): Promise<VerificationContract> {
    try {
      const res = await apiClient.post(`/verification/contracts/${id}/reject`, { reason });
      return res.data;
    } catch {
      const list = localStore.getVerifications().map((v) =>
        v.id === id
          ? {
              ...v,
              status: 'rejected' as const,
              approved_by: 'Alex Mercer (Platform Admin)',
              approved_at: new Date().toISOString(),
            }
          : v
      );
      localStore.setVerifications(list);
      const updated = list.find((v) => v.id === id);
      if (!updated) throw new Error('Contract verification not found');
      return updated;
    }
  },
};
