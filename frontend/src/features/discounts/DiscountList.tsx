import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Percent, Plus, Tag, Check, Calendar } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { settingsService } from '../../services/settingsService';
import { Discount } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

export const DiscountList: React.FC = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [discountType, setDiscountType] = useState<'percentage' | 'fixed_amount'>('percentage');
  const [value, setValue] = useState(15);
  const [validUntil, setValidUntil] = useState('2026-12-31');

  const { data: discounts = [], isLoading } = useQuery({
    queryKey: ['discounts'],
    queryFn: () => settingsService.getDiscounts(),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      settingsService.createDiscount({
        code: code.toUpperCase(),
        name,
        discount_type: discountType,
        value,
        valid_from: new Date().toISOString(),
        valid_until: new Date(validUntil).toISOString(),
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
      setIsCreateOpen(false);
      setCode('');
      setName('');
    },
  });

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Invoices', path: '/admin/invoices' },
          { label: 'Payments & Reconciliation', path: '/admin/payments' },
          { label: 'Automated Billing Runs', path: '/admin/billing' },
          { label: 'Discount Rules', path: '/admin/discounts', badge: `${discounts.length}` },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Promotional Coupons & Plan Discounts
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure promotional percentage cuts, enterprise bill credits, and redemption limits
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-3.5 w-3.5" />}>
          Create Coupon
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Coupon Code</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Discount Value</TableHead>
            <TableHead>Valid Until</TableHead>
            <TableHead>Redemptions</TableHead>
            <TableHead className="text-right">Status</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={3} />
        ) : discounts.length === 0 ? (
          <TableEmpty
            title="No discounts active"
            description="Create coupons to apply promotional credits on quotations and subscriptions."
            actionText="Create Coupon"
            onAction={() => setIsCreateOpen(true)}
            colSpan={7}
          />
        ) : (
          <TableBody>
            {discounts.map((d) => (
              <TableRow key={d.id}>
                <TableCell className="font-mono text-xs font-bold text-brand-600">
                  <div className="flex items-center gap-2">
                    <Tag className="h-3.5 w-3.5" />
                    {d.code}
                  </div>
                </TableCell>
                <TableCell className="text-xs font-semibold text-slate-900 dark:text-white">
                  {d.name}
                </TableCell>
                <TableCell className="text-xs capitalize text-slate-500">
                  {d.discount_type.replace('_', ' ')}
                </TableCell>
                <TableCell className="text-xs font-bold text-emerald-600">
                  {d.discount_type === 'percentage' ? `${d.value}% OFF` : `-$${d.value}`}
                </TableCell>
                <TableCell className="text-xs text-slate-500">
                  {formatDate(d.valid_until)}
                </TableCell>
                <TableCell className="text-xs text-slate-600 dark:text-slate-300">
                  {d.redemption_count} {d.max_redemptions ? `/ ${d.max_redemptions}` : ''}
                </TableCell>
                <TableCell className="text-right">
                  <Badge variant={d.is_active ? 'success' : 'default'} size="sm">
                    {d.is_active ? 'ACTIVE' : 'EXPIRED'}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Promotional Discount"
        maxWidth="md"
      >
        <div className="space-y-4">
          <Input
            label="Coupon Code"
            placeholder="e.g. WINTER30"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <Input
            label="Description / Campaign Name"
            placeholder="e.g. End of Year Special"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Discount Type"
              options={[
                { label: 'Percentage (%)', value: 'percentage' },
                { label: 'Fixed Amount ($)', value: 'fixed_amount' },
              ]}
              value={discountType}
              onChange={(e) => setDiscountType(e.target.value as any)}
            />
            <Input
              label="Value"
              type="number"
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
            />
          </div>

          <Input
            label="Expiration Date"
            type="date"
            value={validUntil}
            onChange={(e) => setValidUntil(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!code || !name}
              isLoading={createMutation.isPending}
            >
              Issue Coupon
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
