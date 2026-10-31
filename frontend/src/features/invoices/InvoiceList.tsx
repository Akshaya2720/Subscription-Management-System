import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Receipt,
  Search,
  Filter,
  Eye,
  Printer,
  CheckCircle2,
  DollarSign,
  Download,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { invoiceService } from '../../services/invoiceService';
import { paymentService } from '../../services/paymentService';
import { Invoice, InvoiceStatus } from '../../types';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';

export const InvoiceList: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);
  const [recordPaymentOpen, setRecordPaymentOpen] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [paymentMethod, setPaymentMethod] = useState<'credit_card' | 'bank_transfer' | 'stripe' | 'upi' | 'check'>('stripe');
  const [paymentRef, setPaymentRef] = useState('');

  // Queries
  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices', search, statusFilter],
    queryFn: () => invoiceService.getInvoices(search, statusFilter),
  });

  // Record Payment Mutation
  const paymentMutation = useMutation({
    mutationFn: () => {
      if (!viewingInvoice) throw new Error('No invoice selected');
      return paymentService.recordPayment({
        invoice_id: viewingInvoice.id,
        amount: paymentAmount || viewingInvoice.balance_due,
        payment_method: paymentMethod,
        reference: paymentRef || `MANUAL-${Date.now()}`,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardMetrics'] });
      setRecordPaymentOpen(false);
      setViewingInvoice(null);
    },
  });

  const handleOpenInvoice = (inv: Invoice) => {
    setViewingInvoice(inv);
    setPaymentAmount(inv.balance_due);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Invoice Management & Ledger
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Track line-item subtotals, calculated taxes, SLA credits, settlement balances, and printable invoices
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by invoice number or customer name..."
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
            <option value="all">All Invoices</option>
            <option value="draft">Draft</option>
            <option value="confirmed">Confirmed</option>
            <option value="partially_paid">Partially Paid</option>
            <option value="paid">Paid</option>
            <option value="overdue">Overdue</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Invoices Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Invoice #</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Issue Date</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead>Total Amount</TableHead>
            <TableHead>Paid Amount</TableHead>
            <TableHead>Balance Due</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={9} rowsCount={4} />
        ) : invoices.length === 0 ? (
          <TableEmpty
            title="No invoices found"
            description="Trigger a billing run or draft a quotation to generate customer invoices."
            colSpan={9}
          />
        ) : (
          <TableBody>
            {invoices.map((inv) => {
              const badge = getStatusBadgeVariant(inv.status);
              const isOverdue = inv.status === 'overdue';

              return (
                <TableRow key={inv.id}>
                  <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                    <div className="flex items-center gap-2">
                      <Receipt className="h-4 w-4 text-brand-600" />
                      {inv.invoice_number}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">
                    <p className="font-medium text-slate-900 dark:text-white">{inv.customer?.name || 'Customer'}</p>
                    <p className="text-[11px] text-slate-400">{inv.customer?.company_name}</p>
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {formatDate(inv.issue_date)}
                  </TableCell>
                  <TableCell className="text-xs text-slate-500">
                    {formatDate(inv.due_date)}
                  </TableCell>
                  <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                    {formatCurrency(inv.total_amount, inv.currency)}
                  </TableCell>
                  <TableCell className="text-xs text-emerald-600 font-medium">
                    {formatCurrency(inv.paid_amount, inv.currency)}
                  </TableCell>
                  <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                    {formatCurrency(inv.balance_due, inv.currency)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={inv.status === 'paid' ? 'success' : isOverdue ? 'danger' : 'default'} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleOpenInvoice(inv)}
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

      {/* Invoice Detail & Printable Modal */}
      {viewingInvoice && (
        <Modal
          isOpen={!!viewingInvoice}
          onClose={() => setViewingInvoice(null)}
          title={`Invoice ${viewingInvoice.invoice_number}`}
          description={`Customer: ${viewingInvoice.customer?.name} • Issued: ${formatDate(viewingInvoice.issue_date)}`}
          maxWidth="2xl"
        >
          <div className="space-y-6 print:m-0 print:p-0" id="printable-invoice">
            {/* Top Overview Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
              <div>
                <span className="text-[11px] text-slate-500">Subtotal</span>
                <p className="text-sm font-semibold">{formatCurrency(viewingInvoice.subtotal, viewingInvoice.currency)}</p>
              </div>
              <div>
                <span className="text-[11px] text-slate-500">Taxes (8.0%)</span>
                <p className="text-sm font-semibold">{formatCurrency(viewingInvoice.tax_amount, viewingInvoice.currency)}</p>
              </div>
              <div>
                <span className="text-[11px] text-slate-500">Total Invoice</span>
                <p className="text-sm font-bold text-slate-900 dark:text-white">
                  {formatCurrency(viewingInvoice.total_amount, viewingInvoice.currency)}
                </p>
              </div>
              <div>
                <span className="text-[11px] text-slate-500">Balance Due</span>
                <p className="text-sm font-bold text-rose-600">
                  {formatCurrency(viewingInvoice.balance_due, viewingInvoice.currency)}
                </p>
              </div>
            </div>

            {/* Line items table */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Itemized Inclusions & Telemetry Delivery
              </h4>
              <div className="rounded-xl border border-slate-200 overflow-hidden dark:border-slate-800">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 dark:bg-slate-800 dark:border-slate-800">
                    <tr>
                      <th className="p-3 text-left">Service Line Item</th>
                      <th className="p-3 text-right">Quantity</th>
                      <th className="p-3 text-right">Unit Rate</th>
                      <th className="p-3 text-right">Tax</th>
                      <th className="p-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {viewingInvoice.line_items.map((item) => (
                      <tr key={item.id} className="border-b border-slate-100 dark:border-slate-800">
                        <td className="p-3 font-semibold text-slate-900 dark:text-white">
                          {item.description}
                        </td>
                        <td className="p-3 text-right">{item.quantity}</td>
                        <td className="p-3 text-right">{formatCurrency(item.unit_price)}</td>
                        <td className="p-3 text-right">{formatCurrency(item.tax_amount)}</td>
                        <td className="p-3 text-right font-bold">{formatCurrency(item.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions: Print, Record Payment */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrint}
                leftIcon={<Printer className="h-4 w-4" />}
              >
                Download / Print Invoice
              </Button>

              {viewingInvoice.balance_due > 0 ? (
                <Button
                  size="sm"
                  onClick={() => setRecordPaymentOpen(true)}
                  leftIcon={<DollarSign className="h-4 w-4" />}
                >
                  Record Payment ({formatCurrency(viewingInvoice.balance_due)})
                </Button>
              ) : (
                <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" /> Fully Settled
                </span>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Record Payment Sub-Modal */}
      {recordPaymentOpen && viewingInvoice && (
        <Modal
          isOpen={recordPaymentOpen}
          onClose={() => setRecordPaymentOpen(false)}
          title={`Record Payment for ${viewingInvoice.invoice_number}`}
          maxWidth="md"
        >
          <div className="space-y-4">
            <Input
              label="Payment Amount ($)"
              type="number"
              step="0.01"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(Number(e.target.value))}
            />

            <Select
              label="Payment Method"
              options={[
                { label: 'Stripe Online Payment', value: 'stripe' },
                { label: 'Bank Wire / ACH', value: 'bank_transfer' },
                { label: 'Corporate Credit Card', value: 'credit_card' },
                { label: 'UPI / Direct Bank Link', value: 'upi' },
                { label: 'Paper Check', value: 'check' },
              ]}
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as any)}
            />

            <Input
              label="Transaction / Reference ID"
              placeholder="e.g. ACH-WIRE-99201"
              value={paymentRef}
              onChange={(e) => setPaymentRef(e.target.value)}
            />

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setRecordPaymentOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => paymentMutation.mutate()}
                isLoading={paymentMutation.isPending}
              >
                Confirm Payment Receipt
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
