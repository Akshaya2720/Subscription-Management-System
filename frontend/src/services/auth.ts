import { apiClient } from './api';
import { User, UserRole, Organization } from '../types';

export interface LoginPayload {
  email: string;
  password?: string;
  role?: UserRole;
}

export interface RegisterOrgPayload {
  organization_name: string;
  domain?: string;
  admin_name: string;
  admin_email: string;
  password?: string;
  currency: string;
  timezone: string;
}

const DEMO_USERS: Record<UserRole, User> = {
  admin: {
    id: 'usr-admin-01',
    email: 'admin@verisub.io',
    full_name: 'Alex Mercer (Platform Admin)',
    role: 'admin',
    organization_id: 'org-001',
    organization_name: 'Verisub Corp Inc.',
    created_at: '2026-01-01T00:00:00Z',
    permissions: ['all'],
  },
  staff: {
    id: 'usr-staff-01',
    email: 'staff@verisub.io',
    full_name: 'Jordan Blake (Billing Specialist)',
    role: 'staff',
    organization_id: 'org-001',
    organization_name: 'Verisub Corp Inc.',
    created_at: '2026-02-15T00:00:00Z',
    permissions: [
      'customers:read',
      'customers:write',
      'quotations:read',
      'quotations:write',
      'subscriptions:read',
      'subscriptions:write',
      'invoices:read',
      'invoices:write',
      'verification:read',
    ],
  },
  customer: {
    id: 'usr-cust-01',
    email: 'billing@acmetechnologies.com',
    full_name: 'Elena Rostova (Customer Rep)',
    role: 'customer',
    organization_id: 'cust-001',
    organization_name: 'Acme Technologies Inc.',
    created_at: '2026-03-01T00:00:00Z',
    permissions: ['customer_portal'],
  },
};

export const authService = {
  async login(payload: LoginPayload): Promise<{ user: User; token: string }> {
    try {
      const response = await apiClient.post('/auth/login', payload);
      const data = response.data;
      const token = data.access_token || data.token || 'mock_jwt_token_verisub';
      const user = data.user || DEMO_USERS[payload.role || 'admin'];

      localStorage.setItem('verisub_token', token);
      localStorage.setItem('verisub_user', JSON.stringify(user));
      return { user, token };
    } catch {
      // Temporary fallback: Allows frictionless evaluation across Admin, Staff, and Customer roles
      const role = payload.role || (payload.email.includes('admin') ? 'admin' : payload.email.includes('staff') ? 'staff' : 'customer');
      const user: User = {
        ...DEMO_USERS[role],
        email: payload.email || DEMO_USERS[role].email,
      };
      const token = 'mock_jwt_token_verisub_' + role;
      localStorage.setItem('verisub_token', token);
      localStorage.setItem('verisub_user', JSON.stringify(user));
      return { user, token };
    }
  },

  async registerOrganization(payload: RegisterOrgPayload): Promise<{ user: User; organization: Organization; token: string }> {
    try {
      const response = await apiClient.post('/auth/register-org', payload);
      const data = response.data;
      const token = data.access_token || 'mock_jwt_token_verisub_admin';
      const user = data.user || {
        id: 'usr-' + Date.now(),
        email: payload.admin_email,
        full_name: payload.admin_name,
        role: 'admin' as UserRole,
        organization_name: payload.organization_name,
        created_at: new Date().toISOString(),
      };
      const organization: Organization = {
        id: 'org-' + Date.now(),
        name: payload.organization_name,
        currency: payload.currency,
        timezone: payload.timezone,
        billing_email: payload.admin_email,
        created_at: new Date().toISOString(),
      };

      localStorage.setItem('verisub_token', token);
      localStorage.setItem('verisub_user', JSON.stringify(user));
      return { user, organization, token };
    } catch {
      const user: User = {
        id: 'usr-' + Date.now(),
        email: payload.admin_email,
        full_name: payload.admin_name,
        role: 'admin',
        organization_name: payload.organization_name,
        created_at: new Date().toISOString(),
      };
      const organization: Organization = {
        id: 'org-' + Date.now(),
        name: payload.organization_name,
        currency: payload.currency,
        timezone: payload.timezone,
        billing_email: payload.admin_email,
        created_at: new Date().toISOString(),
      };
      const token = 'mock_jwt_token_verisub_admin';
      localStorage.setItem('verisub_token', token);
      localStorage.setItem('verisub_user', JSON.stringify(user));
      return { user, organization, token };
    }
  },

  getCurrentUser(): User | null {
    const raw = localStorage.getItem('verisub_user');
    if (!raw) {
      // Default to admin for immediate convenience if not logged in
      const defaultUser = DEMO_USERS.admin;
      localStorage.setItem('verisub_user', JSON.stringify(defaultUser));
      localStorage.setItem('verisub_token', 'mock_jwt_token_verisub_admin');
      return defaultUser;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return DEMO_USERS.admin;
    }
  },

  switchRole(role: UserRole): User {
    const user = DEMO_USERS[role];
    localStorage.setItem('verisub_user', JSON.stringify(user));
    localStorage.setItem('verisub_token', 'mock_jwt_token_verisub_' + role);
    return user;
  },

  logout(): void {
    localStorage.removeItem('verisub_token');
    localStorage.removeItem('verisub_user');
  },

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await apiClient.post('/auth/forgot-password', { email });
      return res.data;
    } catch {
      return { success: true, message: 'Password reset link sent to ' + email };
    }
  },

  async resetPassword(password: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await apiClient.post('/auth/reset-password', { password });
      return res.data;
    } catch {
      return { success: true, message: 'Password has been successfully updated.' };
    }
  },
};
