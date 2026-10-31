import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Plus, Layers, PauseCircle, RefreshCw } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { productService } from '../../services/productService';
import { formatCurrency } from '../../utils';

const planSchema = z.object({
  product_id: z.string().min(1, 'Product selection is required'),
  name: z.string().min(2, 'Plan name is required'),
  code: z.string().min(2, 'Plan code is required'),
  description: z.string().min(5, 'Description is required'),
  billing_frequency: z.enum(['monthly', 'quarterly', 'annually', 'usage_based']),
  price: z.coerce.number().min(0, 'Price must be >= 0'),
  currency: z.string().min(1, 'Currency is required'),
  minimum_quantity: z.coerce.number().min(1, 'Minimum quantity must be >= 1'),
  pause_allowed: z.boolean(),
  auto_renew: z.boolean(),
  trial_days: z.coerce.number().min(0),
});

type PlanFormData = z.infer<typeof planSchema>;

export const PlanList: React.FC = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: plans = [], isLoading: isPlansLoading } = useQuery({
    queryKey: ['plans'],
    queryFn: () => productService.getPlans(),
  });

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => productService.getProducts(),
  });

  const createMutation = useMutation({
    mutationFn: (data: PlanFormData) => {
      const selectedProd = products.find((p) => p.id === data.product_id);
      return productService.createPlan({
        ...data,
        product_name: selectedProd?.name || 'Product',
        is_active: true,
        features: ['Automated Telemetry Audit', '99.9% Uptime Guarantee'],
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      setIsCreateOpen(false);
      reset();
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PlanFormData>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      currency: 'USD',
      billing_frequency: 'monthly',
      price: 1500,
      minimum_quantity: 1,
      pause_allowed: true,
      auto_renew: true,
      trial_days: 14,
    },
  });

  const onSubmit = (data: PlanFormData) => {
    createMutation.mutate(data);
  };

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Subscriptions', path: '/admin/subscriptions' },
          { label: 'Quotations & Pricing', path: '/admin/quotations' },
          { label: 'Product Catalog & Plans', path: '/admin/plans', badge: `${plans.length}` },
          { label: 'Customers', path: '/admin/customers' },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Subscription Plans & Pricing Tiers
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Configure recurring cadences, trial periods, pause policies, and renewal automation
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-3.5 w-3.5" />}>
          Create Plan
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Plan Name</TableHead>
            <TableHead>Associated Product</TableHead>
            <TableHead>Frequency</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Min Qty</TableHead>
            <TableHead>Pause / Auto-Renew</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        {isPlansLoading ? (
          <TableLoading columnsCount={7} rowsCount={3} />
        ) : plans.length === 0 ? (
          <TableEmpty
            title="No plans"
            description="Create subscription plans to package and price your products."
            actionText="Create First Plan"
            onAction={() => setIsCreateOpen(true)}
            colSpan={7}
          />
        ) : (
          <TableBody>
            {plans.map((p) => (
              <TableRow key={p.id}>
                <TableCell>
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-[#0071e3] border border-blue-100 shadow-2xs">
                      <Layers className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-semibold text-xs text-[#1d1d1f]">{p.name}</p>
                      <p className="text-[11px] text-[#6e6e73] font-mono">{p.code}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-xs text-[#1d1d1f]">
                  {p.product_name || 'General Product'}
                </TableCell>
                <TableCell>
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-[#1d1d1f] capitalize">
                    {p.billing_frequency}
                  </span>
                </TableCell>
                <TableCell className="text-xs font-bold text-[#1d1d1f]">
                  {formatCurrency(p.price, p.currency)}
                </TableCell>
                <TableCell className="text-xs text-[#6e6e73]">
                  {p.minimum_quantity} unit(s)
                </TableCell>
                <TableCell className="text-xs">
                  <div className="flex items-center gap-2">
                    {p.pause_allowed && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700" title="Pause permitted">
                        <PauseCircle className="h-3 w-3" /> Pause
                      </span>
                    )}
                    {p.auto_renew && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700" title="Auto-renewal enabled">
                        <RefreshCw className="h-3 w-3" /> Auto-Renew
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={p.is_active ? 'success' : 'default'} size="sm">
                    {p.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>

      {/* Create Plan Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Subscription Plan"
        description="Establish billing rules and frequency for a catalog product"
        maxWidth="lg"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Select
            label="Target Product"
            options={products.map((prod) => ({ label: prod.name, value: prod.id }))}
            error={errors.product_id?.message}
            {...register('product_id')}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Plan Title"
              placeholder="e.g. Enterprise Tier - Monthly"
              error={errors.name?.message}
              {...register('name')}
            />
            <Input
              label="Plan Code"
              placeholder="e.g. PLAN-ENT-M"
              error={errors.code?.message}
              {...register('code')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Select
              label="Billing Cadence"
              options={[
                { label: 'Monthly', value: 'monthly' },
                { label: 'Quarterly', value: 'quarterly' },
                { label: 'Annually', value: 'annually' },
                { label: 'Usage-Based', value: 'usage_based' },
              ]}
              {...register('billing_frequency')}
            />
            <Input
              label="Contracted Price"
              type="number"
              step="0.01"
              error={errors.price?.message}
              {...register('price')}
            />
            <Input
              label="Min Quantity"
              type="number"
              defaultValue={1}
              error={errors.minimum_quantity?.message}
              {...register('minimum_quantity')}
            />
          </div>

          <Input
            label="Description"
            placeholder="Contractual inclusions, SLA support, and billing terms"
            error={errors.description?.message}
            {...register('description')}
          />

          <div className="grid grid-cols-2 gap-4 rounded-2xl bg-[#f5f5f7] p-4 border border-black/[0.06]">
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1d1d1f]">
              <input type="checkbox" className="rounded text-[#0071e3]" {...register('pause_allowed')} />
              Allow Client Pause
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-[#1d1d1f]">
              <input type="checkbox" className="rounded text-[#0071e3]" {...register('auto_renew')} />
              Enable Auto-Renewal
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-black/[0.06]">
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Plan
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
