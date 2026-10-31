import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Check, X, ArrowRight, FileCheck, Eye, Sparkles } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { quotationService } from '../../services/quotationService';
import { customerService } from '../../services/customerService';
import { productService } from '../../services/productService';
import { Quotation, QuotationStatus } from '../../types';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';

export const QuotationList: React.FC = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [viewingQuotation, setViewingQuotation] = useState<Quotation | null>(null);

  // Form state
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [discountCode, setDiscountCode] = useState('');
  const [validUntil, setValidUntil] = useState('2026-12-31');
  const [notes, setNotes] = useState('');

  // Authoritative Backend Calculation State
  const [backendCalculation, setBackendCalculation] = useState<{
    subtotal: number;
    discount_amount: number;
    tax_amount: number;
    total_amount: number;
  } | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Queries
  const { data: quotations = [], isLoading } = useQuery({
    queryKey: ['quotations'],
    queryFn: () => quotationService.getQuotations(),
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customerService.getCustomers(),
  });

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => productService.getProducts(),
  });

  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: () => productService.getPlans(),
  });

  // Calculate authoritative pricing via backend
  const handleCalculatePricing = async () => {
    const prod = products.find((p) => p.id === selectedProductId);
    const plan = plans.find((p) => p.id === selectedPlanId);
    const unitPrice = plan ? plan.price : prod ? prod.base_price : 1000;

    setIsCalculating(true);
    try {
      const result = await quotationService.calculateAuthoritativePricing({
        items: [
          {
            product_id: selectedProductId,
            plan_id: selectedPlanId,
            quantity,
            unit_price: unitPrice,
          },
        ],
        customer_id: selectedCustomerId,
        discount_code: discountCode,
      });
      setBackendCalculation(result);
    } finally {
      setIsCalculating(false);
    }
  };

  // Convert Quotation to Active Subscription
  const convertMutation = useMutation({
    mutationFn: (id: string) => quotationService.convertToSubscription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      setViewingQuotation(null);
    },
  });

  // Update Status
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: QuotationStatus }) =>
      quotationService.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      if (viewingQuotation) {
        setViewingQuotation((prev) => (prev ? { ...prev, status: statusMutation.variables?.status || prev.status } : null));
      }
    },
  });

  // Create Quotation
  const createMutation = useMutation({
    mutationFn: async () => {
      const prod = products.find((p) => p.id === selectedProductId);
      const plan = plans.find((p) => p.id === selectedPlanId);
      const unitPrice = plan ? plan.price : prod ? prod.base_price : 1000;

      // Always request authoritative calculations from backend
      const calc =
        backendCalculation ||
        (await quotationService.calculateAuthoritativePricing({
          items: [{ product_id: selectedProductId, plan_id: selectedPlanId, quantity, unit_price: unitPrice }],
          customer_id: selectedCustomerId,
          discount_code: discountCode,
        }));

      return quotationService.createQuotation({
        customer_id: selectedCustomerId,
        status: 'sent',
        subtotal: calc.subtotal,
        discount_amount: calc.discount_amount,
        tax_amount: calc.tax_amount,
        total_amount: calc.total_amount,
        currency: 'USD',
        valid_until: validUntil,
        notes,
        items: [
          {
            id: 'item-' + Date.now(),
            product_id: selectedProductId,
            product_name: prod?.name || 'Selected Product',
            plan_id: selectedPlanId,
            plan_name: plan?.name || 'Selected Plan',
            quantity,
            unit_price: unitPrice,
            total_amount: calc.total_amount,
          },
        ],
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      setIsCreateOpen(false);
      setBackendCalculation(null);
    },
  });

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Subscriptions', path: '/admin/subscriptions' },
          { label: 'Quotations & Pricing', path: '/admin/quotations', badge: `${quotations.length}` },
          { label: 'Product Catalog & Plans', path: '/admin/plans' },
          { label: 'Customers', path: '/admin/customers' },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Quotations & Proposals
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Authoritative backend tax and discount computation, quotation lifecycle, and 1-click subscription conversion
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} leftIcon={<Plus className="h-3.5 w-3.5" />}>
          Draft Quotation
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Quotation #</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Valid Until</TableHead>
            <TableHead>Subtotal</TableHead>
            <TableHead>Discount</TableHead>
            <TableHead>Total (With Tax)</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={8} rowsCount={3} />
        ) : quotations.length === 0 ? (
          <TableEmpty
            title="No quotations"
            description="Create a quotation to formalize pricing and convert clients into recurring subscribers."
            actionText="Draft First Quotation"
            onAction={() => setIsCreateOpen(true)}
            colSpan={8}
          />
        ) : (
          <TableBody>
            {quotations.map((q) => {
              const badge = getStatusBadgeVariant(q.status);
              return (
                <TableRow key={q.id}>
                  <TableCell className="font-semibold text-xs text-[#0071e3]">
                    <div className="flex items-center gap-2">
                      <FileCheck className="h-4 w-4 text-[#0071e3]" />
                      {q.quotation_number}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs font-medium text-[#1d1d1f]">
                    {q.customer?.name || 'Client Entity'}
                  </TableCell>
                  <TableCell className="text-xs text-[#6e6e73]">
                    {formatDate(q.valid_until)}
                  </TableCell>
                  <TableCell className="text-xs text-[#1d1d1f]">
                    {formatCurrency(q.subtotal, q.currency)}
                  </TableCell>
                  <TableCell className="text-xs text-emerald-700 font-medium">
                    {q.discount_amount > 0 ? `-${formatCurrency(q.discount_amount, q.currency)}` : '—'}
                  </TableCell>
                  <TableCell className="text-xs font-bold text-[#1d1d1f]">
                    {formatCurrency(q.total_amount, q.currency)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={q.status === 'converted' ? 'success' : q.status === 'approved' ? 'info' : 'default'} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setViewingQuotation(q)}
                        leftIcon={<Eye className="h-3.5 w-3.5" />}
                      >
                        Inspect
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        )}
      </Table>

      {/* Draft Quotation Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Draft Authoritative Quotation"
        description="Select client and catalog items. Disclose taxes and discounts calculated via backend pricing engine."
        maxWidth="xl"
      >
        <div className="space-y-4">
          <Select
            label="Customer Account"
            options={[
              { label: 'Select a customer...', value: '' },
              ...customers.map((c) => ({ label: `${c.name} (${c.company_name})`, value: c.id })),
            ]}
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Product Item"
              options={[
                { label: 'Select product...', value: '' },
                ...products.map((p) => ({ label: `${p.name} ($${p.base_price})`, value: p.id })),
              ]}
              value={selectedProductId}
              onChange={(e) => {
                setSelectedProductId(e.target.value);
                const matchingPlans = plans.filter((pl) => pl.product_id === e.target.value);
                if (matchingPlans.length > 0) setSelectedPlanId(matchingPlans[0].id);
              }}
            />
            <Select
              label="Subscription Plan Tier"
              options={[
                { label: 'Select plan...', value: '' },
                ...plans
                  .filter((p) => !selectedProductId || p.product_id === selectedProductId)
                  .map((p) => ({ label: `${p.name} ($${p.price}/${p.billing_frequency})`, value: p.id })),
              ]}
              value={selectedPlanId}
              onChange={(e) => setSelectedPlanId(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Quantity"
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
            />
            <Input
              label="Discount Code (Optional)"
              placeholder="e.g. AUTUMN26"
              value={discountCode}
              onChange={(e) => setDiscountCode(e.target.value)}
            />
            <Input
              label="Valid Until"
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
            />
          </div>

          {/* Trigger Authoritative Backend Pricing */}
          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCalculatePricing}
              isLoading={isCalculating}
              leftIcon={<Sparkles className="h-3.5 w-3.5 text-[#0071e3]" />}
            >
              Calculate Backend Price & Tax
            </Button>
          </div>

          {/* Authoritative Price Summary Box */}
          {backendCalculation && (
            <div className="rounded-2xl border border-black/[0.08] bg-[#f5f5f7] p-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-[#6e6e73]">
                <span>Subtotal (Authoritative)</span>
                <span className="font-semibold text-[#1d1d1f]">
                  {formatCurrency(backendCalculation.subtotal)}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-emerald-700">
                <span>Calculated Discount</span>
                <span>-{formatCurrency(backendCalculation.discount_amount)}</span>
              </div>
              <div className="flex items-center justify-between text-xs text-[#6e6e73]">
                <span>State & City Tax (8.0%)</span>
                <span>+{formatCurrency(backendCalculation.tax_amount)}</span>
              </div>
              <div className="flex items-center justify-between border-t border-black/[0.06] pt-2 text-sm font-bold text-[#1d1d1f]">
                <span>Total Quotation Commitment</span>
                <span className="text-[#0071e3]">
                  {formatCurrency(backendCalculation.total_amount)}
                </span>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-black/[0.06]">
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!selectedCustomerId || !selectedProductId}
              isLoading={createMutation.isPending}
            >
              Issue Quotation
            </Button>
          </div>
        </div>
      </Modal>

      {/* Quotation Detail Modal */}
      {viewingQuotation && (
        <Modal
          isOpen={!!viewingQuotation}
          onClose={() => setViewingQuotation(null)}
          title={`Quotation: ${viewingQuotation.quotation_number}`}
          description={`Customer: ${viewingQuotation.customer?.name} • Issued: ${formatDate(viewingQuotation.created_at)}`}
          maxWidth="2xl"
        >
          <div className="space-y-6">
            <div className="flex items-center justify-between rounded-2xl bg-[#f5f5f7] border border-black/[0.06] p-4">
              <div>
                <span className="text-xs text-[#6e6e73]">Status</span>
                <div className="mt-1">
                  <Badge variant={viewingQuotation.status === 'converted' ? 'success' : 'default'} size="md">
                    {viewingQuotation.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
              <div>
                <span className="text-xs text-[#6e6e73]">Total Amount</span>
                <p className="text-lg font-bold text-[#0071e3]">
                  {formatCurrency(viewingQuotation.total_amount, viewingQuotation.currency)}
                </p>
              </div>
              <div>
                <span className="text-xs text-[#6e6e73]">Expiry Date</span>
                <p className="text-xs font-semibold text-[#1d1d1f]">
                  {formatDate(viewingQuotation.valid_until)}
                </p>
              </div>
            </div>

            {/* Line items table */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#1d1d1f]">
                Quotation Line Items
              </h4>
              <div className="rounded-2xl border border-black/[0.08] overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#fbfbfd] border-b border-black/[0.06] text-[#6e6e73]">
                    <tr>
                      <th className="p-3 text-left">Description</th>
                      <th className="p-3 text-right">Qty</th>
                      <th className="p-3 text-right">Unit Price</th>
                      <th className="p-3 text-right">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black/[0.04]">
                    {viewingQuotation.items.map((item) => (
                      <tr key={item.id} className="hover:bg-black/[0.01]">
                        <td className="p-3 font-semibold text-[#1d1d1f]">{item.product_name} - {item.plan_name}</td>
                        <td className="p-3 text-right text-[#1d1d1f]">{item.quantity}</td>
                        <td className="p-3 text-right text-[#1d1d1f]">{formatCurrency(item.unit_price)}</td>
                        <td className="p-3 text-right font-bold text-[#1d1d1f]">{formatCurrency(item.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions: Convert to Subscription, Approve, Cancel */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-black/[0.06]">
              <div className="flex gap-2">
                {viewingQuotation.status !== 'approved' && viewingQuotation.status !== 'converted' && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => statusMutation.mutate({ id: viewingQuotation.id, status: 'approved' })}
                    isLoading={statusMutation.isPending}
                    leftIcon={<Check className="h-3.5 w-3.5 text-emerald-600" />}
                  >
                    Mark Approved
                  </Button>
                )}
                {viewingQuotation.status !== 'rejected' && viewingQuotation.status !== 'converted' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => statusMutation.mutate({ id: viewingQuotation.id, status: 'rejected' })}
                    isLoading={statusMutation.isPending}
                    leftIcon={<X className="h-3.5 w-3.5 text-rose-600" />}
                  >
                    Cancel Quotation
                  </Button>
                )}
              </div>

              {viewingQuotation.status !== 'converted' ? (
                <Button
                  size="md"
                  onClick={() => convertMutation.mutate(viewingQuotation.id)}
                  isLoading={convertMutation.isPending}
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  Convert to Active Subscription
                </Button>
              ) : (
                <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                  <Check className="h-4 w-4" /> Active Subscription Established
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
