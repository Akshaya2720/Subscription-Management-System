// Core Domain Types for VERISUB Intelligent Subscription & Billing Verification Platform

export type UserRole = 'admin' | 'staff' | 'customer';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id?: string;
  organization_name?: string;
  avatar_url?: string;
  permissions?: string[];
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  domain?: string;
  currency: string;
  timezone: string;
  tax_id?: string;
  logo_url?: string;
  billing_email: string;
  created_at: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company_name?: string;
  tax_number?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  status: 'active' | 'inactive' | 'archived';
  currency: string;
  total_spend?: number;
  active_subscriptions_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  price_override?: number;
  attributes: Record<string, string>;
  is_active: boolean;
}

export interface Product {
  id: string;
  name: string;
  code: string;
  description: string;
  category?: string;
  is_active: boolean;
  base_price: number;
  currency: string;
  variants: ProductVariant[];
  created_at: string;
  updated_at?: string;
}

export type BillingFrequency = 'monthly' | 'quarterly' | 'annually' | 'usage_based';

export interface Plan {
  id: string;
  product_id: string;
  product_name?: string;
  name: string;
  code: string;
  description: string;
  billing_frequency: BillingFrequency;
  price: number;
  currency: string;
  minimum_quantity: number;
  is_active: boolean;
  pause_allowed: boolean;
  auto_renew: boolean;
  trial_days: number;
  features?: string[];
  created_at: string;
}

export type QuotationStatus = 'draft' | 'sent' | 'approved' | 'rejected' | 'expired' | 'converted';

export interface QuotationItem {
  id: string;
  product_id: string;
  product_name: string;
  plan_id?: string;
  plan_name?: string;
  variant_id?: string;
  quantity: number;
  unit_price: number;
  discount_percentage?: number;
  tax_rate?: number;
  total_amount: number;
}

export interface Quotation {
  id: string;
  quotation_number: string;
  customer_id: string;
  customer?: Customer;
  status: QuotationStatus;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  valid_until: string;
  notes?: string;
  items: QuotationItem[];
  subscription_id?: string;
  created_at: string;
}

export type SubscriptionStatus =
  | 'draft'
  | 'quotation'
  | 'confirmed'
  | 'active'
  | 'paused'
  | 'closed'
  | 'cancelled';

export interface SubscriptionItem {
  id: string;
  product_id: string;
  product_name: string;
  variant_name?: string;
  plan_id: string;
  plan_name: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
}

export interface Subscription {
  id: string;
  subscription_number: string;
  customer_id: string;
  customer?: Customer;
  plan_id: string;
  plan?: Plan;
  status: SubscriptionStatus;
  contracted_price: number;
  billing_frequency: BillingFrequency;
  currency: string;
  start_date: string;
  next_billing_date: string;
  expiry_date?: string;
  pause_date?: string;
  resume_date?: string;
  auto_renew: boolean;
  items: SubscriptionItem[];
  created_at: string;
  updated_at?: string;
}

export interface DigitalTwin {
  subscription_id: string;
  subscription_number: string;
  customer: Customer;
  plan: Plan;
  contracted_price: number;
  billing_frequency: BillingFrequency;
  status: SubscriptionStatus;
  start_date: string;
  next_billing_date: string;
  expiry_date?: string;
  metrics: {
    sla_compliance_rate: number;
    total_service_hours_delivered: number;
    contracted_service_hours: number;
    uptime_percentage: number;
    unresolved_discrepancies: number;
  };
  invoices: Invoice[];
  payments: Payment[];
  verifications: VerificationContract[];
  audit_diffs: {
    timestamp: string;
    field: string;
    old_value: string;
    new_value: string;
    changed_by: string;
  }[];
}

export type InvoiceStatus =
  | 'draft'
  | 'confirmed'
  | 'partially_paid'
  | 'paid'
  | 'overdue'
  | 'cancelled';

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  total_amount: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  subscription_id?: string;
  customer_id: string;
  customer?: Customer;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  currency: string;
  line_items: InvoiceLineItem[];
  created_at: string;
  pdf_url?: string;
}

export type PaymentMethod =
  | 'credit_card'
  | 'bank_transfer'
  | 'stripe'
  | 'upi'
  | 'check';

export type PaymentStatus = 'completed' | 'pending' | 'failed' | 'refunded';

export interface Payment {
  id: string;
  payment_number: string;
  invoice_id: string;
  invoice_number?: string;
  customer_id: string;
  customer?: Customer;
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  reference: string;
  payment_date: string;
  status: PaymentStatus;
  refund_status?: 'none' | 'partial' | 'full';
  notes?: string;
  created_at: string;
}

export interface ReconciliationTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  reference: string;
  status: 'matched' | 'unmatched' | 'duplicate';
  matched_invoice_id?: string;
  matched_invoice_number?: string;
  confidence_score?: number;
}

export interface PaymentReconciliation {
  id: string;
  batch_number: string;
  file_name: string;
  upload_date: string;
  total_records: number;
  matched_count: number;
  unmatched_count: number;
  duplicate_count: number;
  status: 'completed' | 'pending_review' | 'failed';
  transactions: ReconciliationTransaction[];
}

export interface BillingRun {
  id: string;
  run_number: string;
  execution_date: string;
  status: 'running' | 'completed' | 'failed' | 'partial';
  total_due_subscriptions: number;
  successful_invoices: number;
  failed_items: number;
  logs: string[];
  created_at: string;
}

export type VerificationStatus =
  | 'verified'
  | 'discrepancy_detected'
  | 'pending_review'
  | 'approved'
  | 'rejected';

export interface VerificationContract {
  id: string;
  contract_number: string;
  customer_id: string;
  customer?: Customer;
  subscription_id: string;
  service_name: string;
  contract_sla: string;
  expected_service_delivery: string;
  actual_recorded_delivery: string;
  discrepancy_detected: boolean;
  discrepancy_details?: string;
  proposed_credit: number;
  currency: string;
  evidence_references: string[];
  status: VerificationStatus;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
}

export interface AIInsight {
  id: string;
  type: 'anomaly' | 'unusual_billing' | 'unexpected_discount' | 'payment_mismatch' | 'verification_warning';
  severity: 'high' | 'medium' | 'low';
  title: string;
  explanation: string;
  entity_type: 'invoice' | 'subscription' | 'customer' | 'payment';
  entity_id: string;
  entity_reference: string;
  is_reviewed: boolean;
  recommended_action: string;
  created_at: string;
}

export interface AIAssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: string[];
  data_payload?: any;
}

export interface AuditLog {
  id: string;
  actor_name: string;
  actor_email: string;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  entity_name?: string;
  timestamp: string;
  change_summary: string;
  hash_chain_integrity: boolean;
  current_hash: string;
  previous_hash: string;
  blockchain_status: 'not_anchored' | 'pending' | 'confirmed';
  blockchain_tx_hash?: string;
}

export interface DashboardMetrics {
  active_subscriptions: number;
  active_subscriptions_change: number;
  revenue_received: number;
  revenue_change: number;
  outstanding_amount: number;
  outstanding_change: number;
  overdue_invoices: number;
  total_customers: number;
  total_customers_change: number;
  upcoming_renewals: number;
  monthly_revenue: { month: string; revenue: number; target: number }[];
  subscription_growth: { month: string; active: number; new: number; churned: number }[];
  payment_trends: { date: string; volume: number; count: number }[];
  invoice_distribution: { name: string; value: number; color: string }[];
}

export interface Discount {
  id: string;
  code: string;
  name: string;
  discount_type: 'percentage' | 'fixed_amount';
  value: number;
  currency?: string;
  valid_from: string;
  valid_until: string;
  max_redemptions?: number;
  redemption_count: number;
  is_active: boolean;
  applicable_plan_ids?: string[];
  created_at: string;
}

export interface CustomerDispute {
  id: string;
  dispute_number: string;
  customer_id: string;
  invoice_id?: string;
  invoice_number?: string;
  reason: string;
  description: string;
  amount_disputed: number;
  status: 'submitted' | 'under_review' | 'resolved' | 'rejected';
  created_at: string;
  resolution_notes?: string;
}
