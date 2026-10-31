import { apiClient } from './api';
import { Payment, PaymentReconciliation } from '../types';
import { localStore } from './store';

export const paymentService = {
  async getPayments(): Promise<Payment[]> {
    try {
      const res = await apiClient.get('/payments');
      return res.data;
    } catch {
      return localStore.getPayments();
    }
  },

  async recordPayment(payload: {
    invoice_id: string;
    amount: number;
    payment_method: Payment['payment_method'];
    reference: string;
    notes?: string;
  }): Promise<Payment> {
    try {
      const res = await apiClient.post(`/invoices/${payload.invoice_id}/payments`, {
        amount: payload.amount,
        payment_method: payload.payment_method === 'stripe' ? 'SIMULATED' : payload.payment_method.toUpperCase(),
        reference: payload.reference,
        notes: payload.notes,
      });
      return res.data;
    } catch {
      const invoice = localStore.getInvoices().find((i) => i.id === payload.invoice_id);
      if (!invoice) throw new Error('Invoice not found');

      const newPayment: Payment = {
        id: 'pay-' + Date.now(),
        payment_number: `PAY-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        invoice_id: invoice.id,
        invoice_number: invoice.invoice_number,
        customer_id: invoice.customer_id,
        customer: invoice.customer,
        amount: payload.amount,
        currency: invoice.currency,
        payment_method: payload.payment_method,
        reference: payload.reference,
        payment_date: new Date().toISOString(),
        status: 'completed',
        refund_status: 'none',
        notes: payload.notes,
        created_at: new Date().toISOString(),
      };

      // Add to payments list
      const payments = [newPayment, ...localStore.getPayments()];
      localStore.setPayments(payments);

      // Update invoice paid amount and balance
      const newPaidAmount = invoice.paid_amount + payload.amount;
      const newBalance = Math.max(0, invoice.total_amount - newPaidAmount);
      const newStatus = newBalance <= 0 ? 'paid' : 'partially_paid';

      const invoices = localStore.getInvoices().map((inv) =>
        inv.id === invoice.id
          ? {
              ...inv,
              paid_amount: newPaidAmount,
              balance_due: newBalance,
              status: newStatus as typeof inv.status,
            }
          : inv
      );
      localStore.setInvoices(invoices);

      return newPayment;
    }
  },

  async getReconciliation(): Promise<PaymentReconciliation> {
    try {
      const res = await apiClient.get('/payments/reconciliation');
      return res.data;
    } catch {
      return localStore.getReconciliation();
    }
  },

  async uploadReconciliationCsv(fileName: string, recordCount: number): Promise<PaymentReconciliation> {
    try {
      const formData = new FormData();
      formData.append('filename', fileName);
      const res = await apiClient.post('/payments/reconcile-csv', formData);
      return res.data;
    } catch {
      const rec: PaymentReconciliation = {
        id: 'rec-' + Date.now(),
        batch_number: `REC-BATCH-${Math.floor(1000 + Math.random() * 9000)}`,
        file_name: fileName,
        upload_date: new Date().toISOString(),
        total_records: recordCount,
        matched_count: Math.floor(recordCount * 0.9),
        unmatched_count: Math.ceil(recordCount * 0.08),
        duplicate_count: Math.max(1, Math.floor(recordCount * 0.02)),
        status: 'pending_review',
        transactions: [
          {
            id: 'tx-' + Date.now() + '-1',
            date: new Date().toISOString().split('T')[0],
            description: 'ACH DEPOSIT - VERISUB SETTLEMENT',
            amount: 3450.0,
            reference: 'ACH-SETTLE-' + Math.floor(10000 + Math.random() * 90000),
            status: 'matched',
            matched_invoice_number: 'INV-2026-1044',
            confidence_score: 99.2,
          },
          {
            id: 'tx-' + Date.now() + '-2',
            date: new Date().toISOString().split('T')[0],
            description: 'CHECK REF #9901 - PENDING MANUAL ATTRIBUTION',
            amount: 1296.0,
            reference: 'CHK-9901',
            status: 'unmatched',
            confidence_score: 41.5,
          },
          {
            id: 'tx-' + Date.now() + '-3',
            date: new Date().toISOString().split('T')[0],
            description: 'STRIPE REPEAT WEBHOOK IDEMPOTENCY CHECK',
            amount: 500.0,
            reference: 'STRIPE-DUP-881',
            status: 'duplicate',
            confidence_score: 98.4,
          },
        ],
      };
      localStore.setReconciliation(rec);
      return rec;
    }
  },

  async matchTransaction(transactionId: string, invoiceId: string): Promise<PaymentReconciliation> {
    try {
      const res = await apiClient.post('/payments/reconcile/match', { transactionId, invoiceId });
      return res.data;
    } catch {
      const rec = localStore.getReconciliation();
      const invoice = localStore.getInvoices().find((i) => i.id === invoiceId);
      const updatedTx = rec.transactions.map((tx) =>
        tx.id === transactionId
          ? {
              ...tx,
              status: 'matched' as const,
              matched_invoice_id: invoiceId,
              matched_invoice_number: invoice?.invoice_number || 'INV-MANUAL-MATCH',
              confidence_score: 100,
            }
          : tx
      );
      const updatedRec: PaymentReconciliation = {
        ...rec,
        transactions: updatedTx,
        matched_count: rec.matched_count + 1,
        unmatched_count: Math.max(0, rec.unmatched_count - 1),
      };
      localStore.setReconciliation(updatedRec);
      return updatedRec;
    }
  },
};
