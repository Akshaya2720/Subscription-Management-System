import { describe, it, expect } from 'vitest';
import { subscriptionService } from '../services/subscriptionService';

describe('Subscription Management & Digital Twin', () => {
  it('retrieves subscriptions and handles lifecycle pause/resume', async () => {
    const list = await subscriptionService.getSubscriptions();
    expect(list.length).toBeGreaterThan(0);

    const firstSub = list[0];
    const paused = await subscriptionService.pauseSubscription(firstSub.id);
    expect(paused.status).toBe('paused');
    expect(paused.pause_date).toBeDefined();

    const resumed = await subscriptionService.resumeSubscription(firstSub.id);
    expect(resumed.status).toBe('active');
  });

  it('retrieves subscription digital twin with telemetry and SLA metrics', async () => {
    const list = await subscriptionService.getSubscriptions();
    const twin = await subscriptionService.getDigitalTwin(list[0].id);

    expect(twin.subscription_number).toBe(list[0].subscription_number);
    expect(twin.metrics.sla_compliance_rate).toBeDefined();
    expect(twin.metrics.uptime_percentage).toBeGreaterThan(95);
    expect(twin.invoices).toBeDefined();
    expect(twin.audit_diffs.length).toBeGreaterThan(0);
  });
});
