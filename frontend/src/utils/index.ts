import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount?: number | null, currency = 'USD'): string {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '$0.00';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString?: string | null): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateString?: string | null): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function getStatusBadgeVariant(status: string): {
  bg: string;
  text: string;
  border: string;
  label: string;
} {
  const s = status.toLowerCase();
  switch (s) {
    case 'active':
    case 'paid':
    case 'verified':
    case 'approved':
    case 'completed':
      return {
        bg: 'bg-emerald-50',
        text: 'text-emerald-800 font-semibold',
        border: 'border-emerald-200/80',
        label: status.toUpperCase(),
      };
    case 'pending':
    case 'pending_review':
    case 'sent':
    case 'confirmed':
    case 'running':
    case 'in_progress':
      return {
        bg: 'bg-blue-50',
        text: 'text-[#0071e3] font-semibold',
        border: 'border-blue-200/80',
        label: status.replace('_', ' ').toUpperCase(),
      };
    case 'paused':
    case 'partially_paid':
    case 'draft':
      return {
        bg: 'bg-amber-50',
        text: 'text-amber-800 font-semibold',
        border: 'border-amber-200/80',
        label: status.replace('_', ' ').toUpperCase(),
      };
    case 'discrepancy_detected':
    case 'overdue':
    case 'rejected':
    case 'failed':
    case 'cancelled':
    case 'closed':
      return {
        bg: 'bg-rose-50',
        text: 'text-rose-800 font-semibold',
        border: 'border-rose-200/80',
        label: status.replace('_', ' ').toUpperCase(),
      };
    default:
      return {
        bg: 'bg-[#f5f5f7]',
        text: 'text-[#1d1d1f] font-semibold',
        border: 'border-black/[0.08]',
        label: status.toUpperCase(),
      };
  }
}
