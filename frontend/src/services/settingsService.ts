import { apiClient } from './api';
import { Organization, Discount } from '../types';
import { localStore } from './store';

export interface OrgSettingsPayload {
  name: string;
  currency: string;
  timezone: string;
  billing_email: string;
  tax_id?: string;
  grace_period_days: number;
  auto_retry_failed_payments: boolean;
  max_retry_attempts: number;
  tax_rate_default: number;
}

export const defaultSettings: OrgSettingsPayload = {
  name: 'Verisub Enterprise Inc.',
  currency: 'USD',
  timezone: 'America/New_York (UTC-5)',
  billing_email: 'billing@verisub.io',
  tax_id: 'US-EIN-94819028',
  grace_period_days: 7,
  auto_retry_failed_payments: true,
  max_retry_attempts: 3,
  tax_rate_default: 8.0,
};

export const settingsService = {
  async getSettings(): Promise<OrgSettingsPayload> {
    try {
      const res = await apiClient.get('/settings/organization');
      return res.data;
    } catch {
      const stored = localStorage.getItem('verisub_org_settings');
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch {
          return defaultSettings;
        }
      }
      return defaultSettings;
    }
  },

  async updateSettings(payload: Partial<OrgSettingsPayload>): Promise<OrgSettingsPayload> {
    try {
      const res = await apiClient.put('/settings/organization', payload);
      return res.data;
    } catch {
      const current = await this.getSettings();
      const updated = { ...current, ...payload };
      localStorage.setItem('verisub_org_settings', JSON.stringify(updated));
      return updated;
    }
  },

  async getDiscounts(): Promise<Discount[]> {
    try {
      const res = await apiClient.get('/discounts');
      return res.data;
    } catch {
      return localStore.getDiscounts();
    }
  },

  async createDiscount(payload: Omit<Discount, 'id' | 'redemption_count' | 'created_at'>): Promise<Discount> {
    try {
      const res = await apiClient.post('/discounts', payload);
      return res.data;
    } catch {
      const newDiscount: Discount = {
        ...payload,
        id: 'disc-' + Date.now(),
        redemption_count: 0,
        created_at: new Date().toISOString(),
      };
      const list = [newDiscount, ...localStore.getDiscounts()];
      localStore.setDiscounts(list);
      return newDiscount;
    }
  },
};
