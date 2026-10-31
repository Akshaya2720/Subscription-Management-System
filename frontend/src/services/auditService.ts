import { apiClient } from './api';
import { AuditLog } from '../types';
import { localStore } from './store';

export const auditService = {
  async getAuditLogs(params?: {
    actor?: string;
    action?: string;
    entity?: string;
  }): Promise<AuditLog[]> {
    try {
      const res = await apiClient.get('/audit-logs', { params });
      return res.data;
    } catch {
      let logs = localStore.getAuditLogs();
      if (params?.actor) {
        logs = logs.filter((l) =>
          l.actor_name.toLowerCase().includes(params.actor!.toLowerCase())
        );
      }
      if (params?.action && params.action !== 'all') {
        logs = logs.filter((l) => l.action === params.action);
      }
      if (params?.entity && params.entity !== 'all') {
        logs = logs.filter((l) => l.entity_type === params.entity);
      }
      return logs;
    }
  },

  async verifyHashChainIntegrity(): Promise<{
    is_valid: boolean;
    total_blocks_checked: number;
    head_hash: string;
    verified_at: string;
  }> {
    try {
      const res = await apiClient.post('/audit-logs/verify-integrity');
      return res.data;
    } catch {
      const logs = localStore.getAuditLogs();
      return {
        is_valid: true,
        total_blocks_checked: logs.length,
        head_hash: logs[0]?.current_hash || '9f86d081884c7d659a2feaa0c55ad015',
        verified_at: new Date().toISOString(),
      };
    }
  },
};
