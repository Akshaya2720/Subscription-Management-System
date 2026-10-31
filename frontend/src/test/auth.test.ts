import { describe, it, expect, beforeEach } from 'vitest';
import { authService } from '../services/auth';

describe('Authentication Service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('authenticates admin persona with appropriate permissions', async () => {
    const { user, token } = await authService.login({
      email: 'admin@verisub.io',
      role: 'admin',
    });

    expect(user.role).toBe('admin');
    expect(token).toBeDefined();
    expect(localStorage.getItem('verisub_token')).toBe(token);
    expect(user.permissions).toContain('all');
  });

  it('authenticates staff persona with restricted permissions', async () => {
    const { user } = await authService.login({
      email: 'staff@verisub.io',
      role: 'staff',
    });

    expect(user.role).toBe('staff');
    expect(user.permissions).toContain('customers:read');
    expect(user.permissions).not.toContain('all');
  });

  it('switches roles dynamically for evaluation simulation', () => {
    const staffUser = authService.switchRole('staff');
    expect(staffUser.role).toBe('staff');

    const customerUser = authService.switchRole('customer');
    expect(customerUser.role).toBe('customer');

    const adminUser = authService.switchRole('admin');
    expect(adminUser.role).toBe('admin');
  });

  it('clears credentials on logout', () => {
    authService.login({ email: 'admin@verisub.io', role: 'admin' });
    authService.logout();
    expect(localStorage.getItem('verisub_token')).toBeNull();
  });
});
