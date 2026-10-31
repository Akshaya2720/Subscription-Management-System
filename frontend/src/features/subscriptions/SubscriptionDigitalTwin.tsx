import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Repeat,
  DollarSign,
  Activity,
  History,
  ShieldCheck,
  Receipt,
  CreditCard,
  Layers,
  Building,
  CheckCircle2,
  AlertTriangle,
  Cpu,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { SubscriptionTimeline } from '../../components/common/Timeline';
import { subscriptionService } from '../../services/subscriptionService';
import { formatCurrency, formatDate } from '../../utils';

export interface SubscriptionDigitalTwinProps {
  subscriptionId: string;
  onClose?: () => void;
}

export const SubscriptionDigitalTwin: React.FC<SubscriptionDigitalTwinProps> = ({
  subscriptionId,
  onClose,
}) => {
  const { data: twin, isLoading, error } = useQuery({
    queryKey: ['digitalTwin', subscriptionId],
    queryFn: () => subscriptionService.getDigitalTwin(subscriptionId),
  });

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center space-y-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  if (error || !twin) {
    return (
      <div className="rounded-xl bg-rose-50 p-6 text-center text-rose-700">
        Failed to fetch Subscription Digital Twin telemetry.
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 p-6 text-white shadow-xl">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/20 text-brand-400 border border-brand-500/30">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight">
                Digital Twin: {twin.subscription_number}
              </h2>
              <Badge variant="purple" size="sm">LIVE TWIN</Badge>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Real-time contract state, telemetry reconciliations & multi-source billing ledger
            </p>
          </div>
        </div>
        {onClose && (
          <Button variant="outline" size="sm" onClick={onClose} className="border-slate-700 text-white hover:bg-slate-800">
            Exit Twin View
          </Button>
        )}
      </div>

      {/* Visual Lifecycle Timeline */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Contract Lifecycle State Progression</CardTitle>
          <CardDescription>Verified cryptographic stage transitions</CardDescription>
        </CardHeader>
        <CardContent>
          <SubscriptionTimeline currentStatus={twin.status} />
        </CardContent>
      </Card>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Contracted Price</span>
            <DollarSign className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(twin.contracted_price)}
            <span className="text-xs font-normal text-slate-500">/{twin.billing_frequency}</span>
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>SLA Compliance</span>
            <Activity className="h-4 w-4 text-brand-500" />
          </div>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {twin.metrics.sla_compliance_rate}%
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Uptime: {twin.metrics.uptime_percentage}%</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Delivered Hours</span>
            <CheckCircle2 className="h-4 w-4 text-blue-500" />
          </div>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {twin.metrics.total_service_hours_delivered} hrs
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Target: {twin.metrics.contracted_service_hours} hrs</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Discrepancies</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <p className="mt-2 text-xl font-bold text-slate-900 dark:text-white">
            {twin.metrics.unresolved_discrepancies}
          </p>
          <p className="text-[11px] text-amber-600 mt-1">Contract-to-bill delta</p>
        </div>
      </div>

      {/* Customer & Plan Metadata Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-brand-600" />
              <CardTitle>Client Entity</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Company Name</span>
              <span className="font-semibold text-slate-900 dark:text-white">{twin.customer.company_name || twin.customer.name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Primary Contact</span>
              <span className="text-slate-900 dark:text-white">{twin.customer.name} ({twin.customer.email})</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Tax / VAT ID</span>
              <span className="font-mono text-slate-900 dark:text-white">{twin.customer.tax_number || 'N/A'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Billing Currency</span>
              <span className="font-bold text-slate-900 dark:text-white">{twin.customer.currency}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-brand-600" />
              <CardTitle>Plan & Billing Schedule</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Plan Code</span>
              <span className="font-mono font-semibold text-slate-900 dark:text-white">{twin.plan.code}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Contract Start Date</span>
              <span className="text-slate-900 dark:text-white">{formatDate(twin.start_date)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
              <span className="text-slate-500">Next Scheduled Billing Run</span>
              <span className="font-bold text-brand-600 dark:text-brand-400">{formatDate(twin.next_billing_date)}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Expiry / Term</span>
              <span className="text-slate-900 dark:text-white">{formatDate(twin.expiry_date)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invoice & Payment History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Receipt className="h-4 w-4 text-brand-600" />
              <CardTitle>Linked Invoices</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {twin.invoices.length === 0 ? (
              <p className="p-4 text-xs text-slate-400">No invoices generated yet.</p>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                {twin.invoices.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between p-3.5">
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">{inv.invoice_number}</p>
                      <p className="text-[11px] text-slate-400">Due {formatDate(inv.due_date)}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-slate-900 dark:text-white">{formatCurrency(inv.total_amount)}</p>
                      <Badge variant={inv.status === 'paid' ? 'success' : 'default'} size="sm">
                        {inv.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Change History & Audit Diff */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-brand-600" />
              <CardTitle>Change History & Audit Diffs</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
              {twin.audit_diffs.map((diff, i) => (
                <div key={i} className="p-3.5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                      Modified [{diff.field}]
                    </span>
                    <span className="text-[11px] text-slate-400">{formatDate(diff.timestamp)}</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    <span className="line-through text-rose-500">{diff.old_value}</span> →{' '}
                    <span className="font-semibold text-emerald-600">{diff.new_value}</span>
                  </p>
                  <p className="text-[10px] text-slate-400">Changed by: {diff.changed_by}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
