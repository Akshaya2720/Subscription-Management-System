import { describe, it, expect } from 'vitest';
import { quotationService } from '../services/quotationService';

describe('Quotation Workflow & Authoritative Calculations', () => {
  it('requests authoritative tax and discount calculation from backend', async () => {
    const calc = await quotationService.calculateAuthoritativePricing({
      items: [
        {
          product_id: 'prod-001',
          plan_id: 'plan-001',
          quantity: 2,
          unit_price: 2499,
        },
      ],
      customer_id: 'cust-001',
      discount_code: 'AUTUMN26',
    });

    expect(calc.subtotal).toBe(4998);
    expect(calc.discount_amount).toBeGreaterThan(0);
    expect(calc.tax_amount).toBeGreaterThan(0);
    expect(calc.total_amount).toBeCloseTo(calc.subtotal - calc.discount_amount + calc.tax_amount, 2);
  });

  it('converts approved quotation into active subscription', async () => {
    const quotes = await quotationService.getQuotations();
    const approved = quotes.find((q) => q.status === 'approved') || quotes[0];

    const sub = await quotationService.convertToSubscription(approved.id);
    expect(sub.id).toBeDefined();
    expect(sub.status).toBe('active');
    expect(sub.subscription_number).toContain('SUB-2026');
  });
});
