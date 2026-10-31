import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  Activity,
  History,
  Receipt,
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
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#0071e3] border-t-transparent" />
      </div>
    );
  }

  if (error || !twin) {
    return (
      <div className="rounded-2xl bg-rose-50 border border-rose-200 p-6 text-center text-rose-700">
        Failed to fetch Subscription Digital Twin telemetry.
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl bg-white border border-black/[0.08] p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-[#0071e3] border border-blue-100 shadow-2xs">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-[#1d1d1f]">
                Digital Twin: {twin.subscription_number}
              </h2>
              <Badge variant="info" size="sm">LIVE TWIN</Badge>
            </div>
            <p className="text-xs text-[#6e6e73] mt-0.5">
              Real-time contract state, telemetry reconciliations & multi-source billing ledger
            </p>
          </div>
        </div>
        {onClose && (
          <Button variant="outline" size="sm" onClick={onClose}>
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
        <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Contracted Price</span>
            <DollarSign className="h-4 w-4 text-emerald-600" />
          </div>
          <p className="mt-2 text-xl font-bold text-[#1d1d1f]">
            {formatCurrency(twin.contracted_price)}
            <span className="text-xs font-normal text-[#6e6e73]">/{twin.billing_frequency}</span>
          </p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>SLA Compliance</span>
            <Activity className="h-4 w-4 text-[#0071e3]" />
          </div>
          <p className="mt-2 text-xl font-bold text-[#1d1d1f]">
            {twin.metrics.sla_compliance_rate}%
          </p>
          <p className="text-[11px] text-[#6e6e73] mt-1">Uptime: {twin.metrics.uptime_percentage}%</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Delivered Hours</span>
            <CheckCircle2 className="h-4 w-4 text-[#0071e3]" />
          </div>
          <p className="mt-2 text-xl font-bold text-[#1d1d1f]">
            {twin.metrics.total_service_hours_delivered} hrs
          </p>
          <p className="text-[11px] text-[#6e6e73] mt-1">Target: {twin.metrics.contracted_service_hours} hrs</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Discrepancies</span>
            <AlertTriangle className="h-4 w-4 text-amber-600" />
          </div>
          <p className="mt-2 text-xl font-bold text-[#1d1d1f]">
            {twin.metrics.unresolved_discrepancies}
          </p>
          <p className="text-[11px] text-amber-700 mt-1">Contract-to-bill delta</p>
        </div>
      </div>

      {/* Customer & Plan Metadata Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Client Entity</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Company Name</span>
              <span className="font-semibold text-[#1d1d1f]">{twin.customer.company_name || twin.customer.name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Primary Contact</span>
              <span className="text-[#1d1d1f]">{twin.customer.name} ({twin.customer.email})</span>
            </div>
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Tax / VAT ID</span>
              <span className="font-mono text-[#1d1d1f]">{twin.customer.tax_number || 'N/A'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#6e6e73]">Billing Currency</span>
              <span className="font-bold text-[#1d1d1f]">{twin.customer.currency}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Plan & Billing Schedule</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Plan Code</span>
              <span className="font-mono font-semibold text-[#1d1d1f]">{twin.plan.code}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Contract Start Date</span>
              <span className="text-[#1d1d1f]">{formatDate(twin.start_date)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-black/[0.05]">
              <span className="text-[#6e6e73]">Next Scheduled Billing Run</span>
              <span className="font-bold text-[#0071e3]">{formatDate(twin.next_billing_date)}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#6e6e73]">Expiry / Term</span>
              <span className="text-[#1d1d1f]">{formatDate(twin.expiry_date)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invoice & Payment History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Receipt className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Linked Invoices</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {twin.invoices.length === 0 ? (
              <p className="p-4 text-xs text-[#6e6e73]">No invoices generated yet.</p>
            ) : (
              <div className="divide-y divide-black/[0.05] text-xs">
                {twin.invoices.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between p-3.5">
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
            )}
          </CardContent>
        </Card>

        {/* Change History & Audit Diff */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-[#0071e3]" />
              <CardTitle>Change History & Audit Diffs</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-black/[0.05] text-xs">
              {twin.audit_diffs.map((diff, i) => (
                <div key={i} className="p-3.5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-[#1d1d1f]">
                      Modified [{diff.field}]
                    </span>
                    <span className="text-[11px] text-[#6e6e73]">{formatDate(diff.timestamp)}</span>
                  </div>
                  <p className="text-[11px] text-[#6e6e73]">
                    <span className="line-through text-rose-500">{diff.old_value}</span> →{' '}
                    <span className="font-semibold text-emerald-700">{diff.new_value}</span>
                  </p>
                  <p className="text-[10px] text-[#86868b]">Changed by: {diff.changed_by}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
