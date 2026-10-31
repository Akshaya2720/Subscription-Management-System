import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Repeat,
  Pause,
  Play,
  RefreshCw,
  XCircle,
  Eye,
  Cpu,
  Search,
  Filter,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { SubscriptionTimeline } from '../../components/common/Timeline';
import { SubscriptionDigitalTwin } from './SubscriptionDigitalTwin';
import { subscriptionService } from '../../services/subscriptionService';
import { customerService } from '../../services/customerService';
import { productService } from '../../services/productService';
import { Subscription, SubscriptionStatus } from '../../types';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';

export const SubscriptionList: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [digitalTwinId, setDigitalTwinId] = useState<string | null>(null);

  // Form states
  const [customerId, setCustomerId] = useState('');
  const [planId, setPlanId] = useState('');
  const [contractedPrice, setContractedPrice] = useState(2499);
  const [billingFrequency, setBillingFrequency] = useState<'monthly' | 'quarterly' | 'annually' | 'usage_based'>('monthly');

  // Queries
  const { data: subscriptions = [], isLoading } = useQuery({
    queryKey: ['subscriptions', search, statusFilter],
    queryFn: () => subscriptionService.getSubscriptions(search, statusFilter),
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customerService.getCustomers(),
  });

  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: () => productService.getPlans(),
  });

  // Lifecycle Mutations
  const pauseMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.pauseSubscription(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.resumeSubscription(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  });

  const renewMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.renewSubscription(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.closeSubscription(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  });

  const createMutation = useMutation({
    mutationFn: () => {
      const selectedPlan = plans.find((p) => p.id === planId);
      return subscriptionService.createSubscription({
        customer_id: customerId,
        plan_id: planId,
        status: 'active',
        contracted_price: contractedPrice,
        billing_frequency: billingFrequency,
        currency: 'USD',
        start_date: new Date().toISOString(),
        next_billing_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        auto_renew: true,
        items: [
          {
            id: 'item-' + Date.now(),
            product_id: selectedPlan?.product_id || 'prod-001',
            product_name: selectedPlan?.product_name || 'Enterprise Service',
            plan_id: planId,
            plan_name: selectedPlan?.name || 'Standard Tier',
            quantity: 1,
            unit_price: contractedPrice,
            total_amount: contractedPrice,
          },
        ],
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      setIsCreateOpen(false);
    },
  });

  if (digitalTwinId) {
    return (
      <SubscriptionDigitalTwin
        subscriptionId={digitalTwinId}
        onClose={() => setDigitalTwinId(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Subscription Operations & Digital Twin
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage contract lifecycle (Pause, Resume, Renew, Close) and inspect telemetry digital twins
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
          New Subscription
        </Button>
      </div>

      {/* Visual Timeline Showcase */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Automated Contract State Progression
          </span>
          <span className="text-[11px] text-slate-400">Framer Motion Transitions</span>
        </div>
        <SubscriptionTimeline currentStatus="active" />
      </div>

      {/* Search & Status Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by subscription number or customer..."
            className="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-4 w-4 text-slate-400 shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 outline-none focus:border-brand-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 w-full sm:w-auto"
          >
            <option value="all">All States</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="confirmed">Confirmed</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Subscriptions Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Subscription #</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Contracted Price</TableHead>
            <TableHead>Cadence</TableHead>
            <TableHead>Next Billing</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Lifecycle Actions</TableHead>
            <TableHead className="text-right">Digital Twin</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={8} rowsCount={4} />
        ) : subscriptions.length === 0 ? (
          <TableEmpty
            title="No subscriptions found"
            description="Create a subscription or convert an approved quotation."
            actionText="Create Subscription"
            onAction={() => setIsCreateOpen(true)}
            colSpan={8}
          />
        ) : (
          <TableBody>
            {subscriptions.map((s) => {
              const badge = getStatusBadgeVariant(s.status);
              const isActive = s.status === 'active';
              const isPaused = s.status === 'paused';
              const isClosed = s.status === 'closed';

              return (
                <TableRow key={s.id}>
                  <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                    <div className="flex items-center gap-2">
                      <Repeat className="h-4 w-4 text-brand-600" />
                      {s.subscription_number}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">
                    <p className="font-medium text-slate-900 dark:text-white">{s.customer?.name || 'Customer'}</p>
                    <p className="text-[11px] text-slate-400">{s.customer?.company_name}</p>
                  </TableCell>
                  <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                    {formatCurrency(s.contracted_price, s.currency)}
                  </TableCell>
                  <TableCell className="text-xs capitalize text-slate-600 dark:text-slate-300">
                    {s.billing_frequency}
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {formatDate(s.next_billing_date)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={isActive ? 'success' : isPaused ? 'warning' : 'default'} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>

                  {/* Lifecycle Controls */}
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      {isActive && (
                        <button
                          onClick={() => pauseMutation.mutate(s.id)}
                          className="flex items-center gap-1 rounded bg-amber-50 px-2 py-1 text-[11px] font-semibold text-amber-700 hover:bg-amber-100 dark:bg-amber-950/40 dark:text-amber-300"
                          title="Pause subscription billing"
                        >
                          <Pause className="h-3 w-3" /> Pause
                        </button>
                      )}

                      {isPaused && (
                        <button
                          onClick={() => resumeMutation.mutate(s.id)}
                          className="flex items-center gap-1 rounded bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-300"
                          title="Resume subscription billing"
                        >
                          <Play className="h-3 w-3" /> Resume
                        </button>
                      )}

                      {!isClosed && (
                        <button
                          onClick={() => renewMutation.mutate(s.id)}
                          className="flex items-center gap-1 rounded bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                          title="Trigger renewal"
                        >
                          <RefreshCw className="h-3 w-3" /> Renew
                        </button>
                      )}

                      {!isClosed && (
                        <button
                          onClick={() => closeMutation.mutate(s.id)}
                          className="rounded p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                          title="Close / Cancel"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </TableCell>

                  {/* Digital Twin Button */}
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setDigitalTwinId(s.id)}
                      leftIcon={<Cpu className="h-3.5 w-3.5 text-brand-600" />}
                    >
                      Digital Twin
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        )}
      </Table>

      {/* Create Subscription Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Establish Subscription Contract"
        description="Bind a client to a recurring service plan with SLA verification telemetry"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <Select
            label="Customer"
            options={[
              { label: 'Select client account...', value: '' },
              ...customers.map((c) => ({ label: `${c.name} (${c.company_name})`, value: c.id })),
            ]}
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          />

          <Select
            label="Plan Tier"
            options={[
              { label: 'Select plan...', value: '' },
              ...plans.map((p) => ({ label: `${p.name} ($${p.price}/${p.billing_frequency})`, value: p.id })),
            ]}
            value={planId}
            onChange={(e) => {
              setPlanId(e.target.value);
              const selected = plans.find((p) => p.id === e.target.value);
              if (selected) {
                setContractedPrice(selected.price);
                setBillingFrequency(selected.billing_frequency);
              }
            }}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contracted Price"
              type="number"
              step="0.01"
              value={contractedPrice}
              onChange={(e) => setContractedPrice(Number(e.target.value))}
            />
            <Select
              label="Billing Frequency"
              options={[
                { label: 'Monthly', value: 'monthly' },
                { label: 'Quarterly', value: 'quarterly' },
                { label: 'Annually', value: 'annually' },
                { label: 'Usage-Based', value: 'usage_based' },
              ]}
              value={billingFrequency}
              onChange={(e) => setBillingFrequency(e.target.value as any)}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!customerId || !planId}
              isLoading={createMutation.isPending}
            >
              Activate Subscription
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
