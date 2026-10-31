import { describe, it, expect } from 'vitest';
import { customerService } from '../services/customerService';

describe('Customer Management Service', () => {
  it('retrieves customers and supports search filtering', async () => {
    const all = await customerService.getCustomers();
    expect(all.length).toBeGreaterThan(0);

    const filtered = await customerService.getCustomers('Acme');
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered[0].name).toContain('Acme');
  });

  it('creates and updates customer entity', async () => {
    const created = await customerService.createCustomer({
      name: 'Test Partner',
      email: 'test@partner.com',
      company_name: 'Partner LLC',
      country: 'United States',
      status: 'active',
      currency: 'USD',
    });

    expect(created.id).toBeDefined();
    expect(created.name).toBe('Test Partner');

    const updated = await customerService.updateCustomer(created.id, {
      company_name: 'Partner Global LLC',
    });
    expect(updated.company_name).toBe('Partner Global LLC');
  });
});
