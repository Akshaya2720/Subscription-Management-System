import {
  Customer,
  Product,
  Plan,
  Quotation,
  Subscription,
  Invoice,
  Payment,
  VerificationContract,
  AIInsight,
  AuditLog,
  PaymentReconciliation,
  BillingRun,
  Discount,
} from '../types';
import {
  initialCustomers,
  initialProducts,
  initialPlans,
  initialQuotations,
  initialSubscriptions,
  initialInvoices,
  initialPayments,
  initialVerifications,
  initialAIInsights,
  initialAuditLogs,
  initialReconciliation,
  initialBillingRuns,
  initialDiscounts,
} from './fallbackData';

// Storage Keys
const KEYS = {
  CUSTOMERS: 'verisub_customers',
  PRODUCTS: 'verisub_products',
  PLANS: 'verisub_plans',
  QUOTATIONS: 'verisub_quotations',
  SUBSCRIPTIONS: 'verisub_subscriptions',
  INVOICES: 'verisub_invoices',
  PAYMENTS: 'verisub_payments',
  VERIFICATIONS: 'verisub_verifications',
  AI_INSIGHTS: 'verisub_ai_insights',
  AUDIT_LOGS: 'verisub_audit_logs',
  RECONCILIATION: 'verisub_reconciliation',
  BILLING_RUNS: 'verisub_billing_runs',
  DISCOUNTS: 'verisub_discounts',
};

function getStored<T>(key: string, initial: T): T {
  try {
    const item = localStorage.getItem(key);
    if (!item) {
      localStorage.setItem(key, JSON.stringify(initial));
      return initial;
    }
    return JSON.parse(item);
  } catch {
    return initial;
  }
}

function setStored<T>(key: string, data: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error(`Failed to store key ${key}:`, e);
  }
}

export const localStore = {
  getCustomers: (): Customer[] => getStored(KEYS.CUSTOMERS, initialCustomers),
  setCustomers: (data: Customer[]) => setStored(KEYS.CUSTOMERS, data),

  getProducts: (): Product[] => getStored(KEYS.PRODUCTS, initialProducts),
  setProducts: (data: Product[]) => setStored(KEYS.PRODUCTS, data),

  getPlans: (): Plan[] => getStored(KEYS.PLANS, initialPlans),
  setPlans: (data: Plan[]) => setStored(KEYS.PLANS, data),

  getQuotations: (): Quotation[] => getStored(KEYS.QUOTATIONS, initialQuotations),
  setQuotations: (data: Quotation[]) => setStored(KEYS.QUOTATIONS, data),

  getSubscriptions: (): Subscription[] => getStored(KEYS.SUBSCRIPTIONS, initialSubscriptions),
  setSubscriptions: (data: Subscription[]) => setStored(KEYS.SUBSCRIPTIONS, data),

  getInvoices: (): Invoice[] => getStored(KEYS.INVOICES, initialInvoices),
  setInvoices: (data: Invoice[]) => setStored(KEYS.INVOICES, data),

  getPayments: (): Payment[] => getStored(KEYS.PAYMENTS, initialPayments),
  setPayments: (data: Payment[]) => setStored(KEYS.PAYMENTS, data),

  getVerifications: (): VerificationContract[] => getStored(KEYS.VERIFICATIONS, initialVerifications),
  setVerifications: (data: VerificationContract[]) => setStored(KEYS.VERIFICATIONS, data),

  getAIInsights: (): AIInsight[] => getStored(KEYS.AI_INSIGHTS, initialAIInsights),
  setAIInsights: (data: AIInsight[]) => setStored(KEYS.AI_INSIGHTS, data),

  getAuditLogs: (): AuditLog[] => getStored(KEYS.AUDIT_LOGS, initialAuditLogs),
  setAuditLogs: (data: AuditLog[]) => setStored(KEYS.AUDIT_LOGS, data),

  getReconciliation: (): PaymentReconciliation => getStored(KEYS.RECONCILIATION, initialReconciliation),
  setReconciliation: (data: PaymentReconciliation) => setStored(KEYS.RECONCILIATION, data),

  getBillingRuns: (): BillingRun[] => getStored(KEYS.BILLING_RUNS, initialBillingRuns),
  setBillingRuns: (data: BillingRun[]) => setStored(KEYS.BILLING_RUNS, data),

  getDiscounts: (): Discount[] => getStored(KEYS.DISCOUNTS, initialDiscounts),
  setDiscounts: (data: Discount[]) => setStored(KEYS.DISCOUNTS, data),
};
