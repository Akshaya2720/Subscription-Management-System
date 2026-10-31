import { describe, it, expect } from 'vitest';
import { verificationService } from '../services/verificationService';

describe('Contract-to-Bill Value Verification', () => {
  it('retrieves SLA verification contracts and detects telemetry discrepancies', async () => {
    const list = await verificationService.getVerifications();
    expect(list.length).toBeGreaterThan(0);

    const flagged = list.find((v) => v.discrepancy_detected);
    expect(flagged).toBeDefined();
    expect(flagged?.proposed_credit).toBeGreaterThan(0);
  });

  it('approves service credit adjustments', async () => {
    const list = await verificationService.getVerifications();
    const flagged = list.find((v) => v.discrepancy_detected && v.status === 'pending_review');

    if (flagged) {
      const approved = await verificationService.approveCredit(flagged.id);
      expect(approved.status).toBe('approved');
      expect(approved.approved_by).toBeDefined();
    }
  });
});
