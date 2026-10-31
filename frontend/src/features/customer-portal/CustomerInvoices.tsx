import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Receipt, DollarSign, Printer, CheckCircle2, Eye } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { invoiceService } from '../../services/invoiceService';
import { paymentService } from '../../services/paymentService';
import { Invoice } from '../../types';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';

export const CustomerInvoices: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [payModalOpen, setPayModalOpen] = useState(false);

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['customerInvoices'],
    queryFn: () => invoiceService.getInvoices(),
  });

  const payMutation = useMutation({
    mutationFn: () => {
      if (!selectedInvoice) throw new Error('No invoice selected');
      return paymentService.recordPayment({
        invoice_id: selectedInvoice.id,
        amount: selectedInvoice.balance_due,
        payment_method: 'stripe',
        reference: `ONLINE-PORTAL-${Date.now()}`,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customerInvoices'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setPayModalOpen(false);
      setSelectedInvoice(null);
    },
  });

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Invoices & Billing Statement
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Review itemized charges, download PDF tax receipts, and pay balances directly online
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Invoice #</TableHead>
            <TableHead>Issue Date</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead>Total Amount</TableHead>
            <TableHead>Balance Due</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={3} />
        ) : (
          <TableBody>
            {invoices.map((inv) => {
              const badge = getStatusBadgeVariant(inv.status);
              const hasBalance = inv.balance_due > 0;

              return (
                <TableRow key={inv.id}>
                  <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                    <div className="flex items-center gap-2">
                      <Receipt className="h-4 w-4 text-brand-600" />
                      {inv.invoice_number}
                    </div>
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
                  <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                    {hasBalance ? (
                      <span className="text-rose-600">{formatCurrency(inv.balance_due, inv.currency)}</span>
                    ) : (
                      <span className="text-emerald-600">$0.00</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={inv.status === 'paid' ? 'success' : hasBalance ? 'danger' : 'default'} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setSelectedInvoice(inv)}
                        leftIcon={<Eye className="h-3.5 w-3.5" />}
                      >
                        Inspect
                      </Button>
                      {hasBalance && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setSelectedInvoice(inv);
                            setPayModalOpen(true);
                          }}
                          leftIcon={<DollarSign className="h-3.5 w-3.5" />}
                        >
                          Pay Now
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        )}
      </Table>

      {/* Pay Modal */}
      {payModalOpen && selectedInvoice && (
        <Modal
          isOpen={payModalOpen}
          onClose={() => setPayModalOpen(false)}
          title={`Pay Invoice ${selectedInvoice.invoice_number}`}
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60 text-center">
              <span className="text-xs text-slate-500">Total Settlement Balance</span>
              <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                {formatCurrency(selectedInvoice.balance_due, selectedInvoice.currency)}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">Secured via Stripe Payment Gateway</p>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setPayModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => payMutation.mutate()}
                isLoading={payMutation.isPending}
              >
                Confirm Payment
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Invoice Detail Modal */}
      {selectedInvoice && !payModalOpen && (
        <Modal
          isOpen={!!selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          title={`Tax Invoice: ${selectedInvoice.invoice_number}`}
          maxWidth="xl"
        >
          <div className="space-y-4 text-xs">
            <div className="flex justify-between p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
              <span>Status: <strong className="uppercase">{selectedInvoice.status}</strong></span>
              <span>Total: <strong>{formatCurrency(selectedInvoice.total_amount)}</strong></span>
            </div>
            <div className="border rounded-xl p-3 space-y-2">
              <h5 className="font-bold">Itemized Services:</h5>
              {selectedInvoice.line_items.map((item) => (
                <div key={item.id} className="flex justify-between">
                  <span>{item.description} (x{item.quantity})</span>
                  <span>{formatCurrency(item.total_amount)}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-end pt-3">
              <Button size="sm" variant="outline" onClick={() => window.print()} leftIcon={<Printer className="h-4 w-4" />}>
                Print Receipt
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
