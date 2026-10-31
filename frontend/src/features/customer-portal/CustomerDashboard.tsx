import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Repeat,
  Receipt,
  ShieldCheck,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { subscriptionService } from '../../services/subscriptionService';
import { invoiceService } from '../../services/invoiceService';
import { formatCurrency, formatDate } from '../../utils';
import { Link } from 'react-router-dom';

export const CustomerDashboard: React.FC = () => {
  const { data: subscriptions = [] } = useQuery({
    queryKey: ['customerSubscriptions'],
    queryFn: () => subscriptionService.getSubscriptions(),
  });

  const { data: invoices = [] } = useQuery({
    queryKey: ['customerInvoices'],
    queryFn: () => invoiceService.getInvoices(),
  });

  const activeSub = subscriptions.find((s) => s.status === 'active') || subscriptions[0];
  const pendingInvoices = invoices.filter((i) => i.balance_due > 0);
  const totalBalanceDue = pendingInvoices.reduce((sum, i) => sum + i.balance_due, 0);

  return (
    <div className="space-y-6 text-left">
      {/* Welcome Hero */}
      <div className="rounded-2xl bg-white border border-black/[0.08] p-7 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#0071e3]">
          Customer Self-Service Hub
        </span>
        <h1 className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-[#1d1d1f]">
          Welcome back, Acme Technologies
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-[#6e6e73] max-w-xl">
          Review your contracted service tiers, SLA delivery verifications, automated invoice payments, and open support tickets.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Active Subscriptions</span>
            <Repeat className="h-4 w-4 text-[#0071e3]" />
          </div>
          <p className="mt-2 text-2xl font-bold text-[#1d1d1f]">
            {subscriptions.filter((s) => s.status === 'active').length}
          </p>
          <p className="text-[11px] text-emerald-700 mt-1 font-medium">99.9% Uptime Verified</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Pending Balance</span>
            <Receipt className="h-4 w-4 text-rose-600" />
          </div>
          <p className="mt-2 text-2xl font-bold text-rose-700">
            {formatCurrency(totalBalanceDue)}
          </p>
          <p className="text-[11px] text-[#6e6e73] mt-1">{pendingInvoices.length} invoice(s) due</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>SLA Delivery Compliance</span>
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-700">98.6%</p>
          <p className="text-[11px] text-[#0071e3] mt-1 font-medium">SLA protection active</p>
        </div>
      </div>

      {/* Primary Subscriptions & Invoices Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Plan Detail */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Current Primary Subscription</CardTitle>
              <CardDescription>Enterprise SLA and recurrence details</CardDescription>
            </div>
            <Link to="/portal/subscriptions" className="text-xs text-[#0071e3] hover:underline font-semibold">
              Manage
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeSub ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-2xl bg-[#f5f5f7] border border-black/[0.06] p-4">
                  <div>
                    <h4 className="text-sm font-bold text-[#1d1d1f]">
                      {activeSub.plan?.name || 'Enterprise Cloud Infrastructure'}
                    </h4>
                    <p className="text-xs text-[#6e6e73]">Ref: {activeSub.subscription_number}</p>
                  </div>
                  <Badge variant="success">{activeSub.status.toUpperCase()}</Badge>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 border border-black/[0.06] rounded-xl bg-white">
                    <span className="text-[#6e6e73]">Rate:</span>
                    <p className="font-bold text-[#1d1d1f] mt-0.5">
                      {formatCurrency(activeSub.contracted_price)}/{activeSub.billing_frequency}
                    </p>
                  </div>
                  <div className="p-3 border border-black/[0.06] rounded-xl bg-white">
                    <span className="text-[#6e6e73]">Next Billing Date:</span>
                    <p className="font-bold text-[#1d1d1f] mt-0.5">
                      {formatDate(activeSub.next_billing_date)}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-[#6e6e73]">No active subscriptions registered.</p>
            )}
          </CardContent>
        </Card>

        {/* Recent Invoices */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Invoices</CardTitle>
              <CardDescription>Settlement history and balances</CardDescription>
            </div>
            <Link to="/portal/invoices" className="text-xs text-[#0071e3] hover:underline font-semibold">
              All Invoices
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-black/[0.05] text-xs">
              {invoices.slice(0, 3).map((inv) => (
                <div key={inv.id} className="flex items-center justify-between p-4 hover:bg-black/[0.01]">
                  <div>
                    <p className="font-semibold text-[#1d1d1f]">{inv.invoice_number}</p>
                    <p className="text-[11px] text-[#6e6e73]">Due {formatDate(inv.due_date)}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#1d1d1f]">{formatCurrency(inv.total_amount)}</p>
                    <Badge variant={inv.status === 'paid' ? 'success' : 'default'} size="sm">
                      {inv.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
