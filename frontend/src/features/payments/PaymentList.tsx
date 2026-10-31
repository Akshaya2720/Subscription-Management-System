import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CreditCard,
  Upload,
  Sparkles,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Tabs } from '../../components/common/Tabs';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { paymentService } from '../../services/paymentService';
import { invoiceService } from '../../services/invoiceService';
import { formatCurrency, formatDateTime, getStatusBadgeVariant } from '../../utils';

export const PaymentList: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'payments' | 'reconciliation'>('payments');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedTxForMatch, setSelectedTxForMatch] = useState<string | null>(null);

  // Queries
  const { data: payments = [], isLoading: isPaymentsLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: () => paymentService.getPayments(),
  });

  const { data: reconciliation, isLoading: isRecLoading } = useQuery({
    queryKey: ['reconciliation'],
    queryFn: () => paymentService.getReconciliation(),
  });

  const { data: invoices = [] } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => invoiceService.getInvoices(),
  });

  // Mutations
  const uploadCsvMutation = useMutation({
    mutationFn: () =>
      paymentService.uploadReconciliationCsv('bank_statement_nov_2026.csv', 32),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      setUploadModalOpen(false);
    },
  });

  const matchTxMutation = useMutation({
    mutationFn: ({ txId, invoiceId }: { txId: string; invoiceId: string }) =>
      paymentService.matchTransaction(txId, invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      setSelectedTxForMatch(null);
    },
  });

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Invoices', path: '/admin/invoices' },
          { label: 'Payments & Reconciliation', path: '/admin/payments', badge: `${payments.length}` },
          { label: 'Automated Billing Runs', path: '/admin/billing' },
          { label: 'Discount Rules', path: '/admin/discounts' },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Payments & Bank Reconciliation
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Track customer payments, Stripe & ACH transactions, and automated statement reconciliation
          </p>
        </div>

        {activeTab === 'reconciliation' && (
          <Button
            onClick={() => setUploadModalOpen(true)}
            leftIcon={<Upload className="h-3.5 w-3.5" />}
          >
            Upload Statement CSV
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'payments', label: 'Payment Records', count: payments.length },
          {
            id: 'reconciliation',
            label: 'Automated Reconciliation',
            count: reconciliation?.unmatched_count,
          },
        ]}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {/* TAB 1: Payments List */}
      {activeTab === 'payments' && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Payment #</TableHead>
              <TableHead>Invoice Linked</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Reference ID</TableHead>
              <TableHead>Date & Time</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          {isPaymentsLoading ? (
            <TableLoading columnsCount={8} rowsCount={3} />
          ) : payments.length === 0 ? (
            <TableEmpty
              title="No payments recorded"
              description="Payments will appear here when invoices are settled online or recorded manually."
              colSpan={8}
            />
          ) : (
            <TableBody>
              {payments.map((p) => {
                const badge = getStatusBadgeVariant(p.status);
                return (
                  <TableRow key={p.id}>
                    <TableCell className="font-semibold text-xs text-[#0071e3]">
                      <div className="flex items-center gap-2">
                        <CreditCard className="h-4 w-4 text-[#0071e3]" />
                        {p.payment_number}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs font-mono font-medium text-[#0071e3]">
                      {p.invoice_number || 'INV-SETTLE'}
                    </TableCell>
                    <TableCell className="text-xs font-medium text-[#1d1d1f]">
                      {p.customer?.name || 'Customer Account'}
                    </TableCell>
                    <TableCell className="text-xs capitalize text-[#6e6e73]">
                      {p.payment_method.replace('_', ' ')}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-[#6e6e73]">
                      {p.reference}
                    </TableCell>
                    <TableCell className="text-xs text-[#6e6e73]">
                      {formatDateTime(p.payment_date)}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-[#1d1d1f]">
                      {formatCurrency(p.amount, p.currency)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={p.status === 'completed' ? 'success' : 'default'} size="sm">
                        {badge.label}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          )}
        </Table>
      )}

      {/* TAB 2: Reconciliation Interface */}
      {activeTab === 'reconciliation' && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
              <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Total Transactions</span>
              <p className="mt-1 text-2xl font-bold text-[#1d1d1f]">
                {reconciliation?.total_records || 0}
              </p>
              <p className="text-[11px] text-[#6e6e73] mt-0.5">{reconciliation?.file_name}</p>
            </div>

            <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
              <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Auto-Matched</span>
              <p className="mt-1 text-2xl font-bold text-emerald-700">
                {reconciliation?.matched_count || 0}
              </p>
              <p className="text-[11px] text-emerald-700 mt-0.5 font-medium">High confidence &gt; 98%</p>
            </div>

            <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
              <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Unmatched (Review)</span>
              <p className="mt-1 text-2xl font-bold text-amber-700">
                {reconciliation?.unmatched_count || 0}
              </p>
              <p className="text-[11px] text-amber-700 mt-0.5 font-medium">Requires manual attribution</p>
            </div>

            <div className="rounded-2xl border border-black/[0.08] bg-white p-4 shadow-2xs">
              <span className="text-[11px] font-semibold text-[#6e6e73] uppercase">Potential Duplicates</span>
              <p className="mt-1 text-2xl font-bold text-rose-700">
                {reconciliation?.duplicate_count || 0}
              </p>
              <p className="text-[11px] text-rose-700 mt-0.5 font-medium">Flagged for deduplication</p>
            </div>
          </div>

          {/* Transactions Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transaction Date</TableHead>
                <TableHead>Statement Description</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Matched Invoice</TableHead>
                <TableHead>Reconciliation Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            {isRecLoading ? (
              <TableLoading columnsCount={7} rowsCount={3} />
            ) : !reconciliation?.transactions.length ? (
              <TableEmpty title="No reconciliation records" description="Upload a CSV bank feed to begin matching." colSpan={7} />
            ) : (
              <TableBody>
                {reconciliation.transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell className="text-xs text-[#6e6e73]">{tx.date}</TableCell>
                    <TableCell className="text-xs font-semibold text-[#1d1d1f]">
                      {tx.description}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-[#6e6e73]">{tx.reference}</TableCell>
                    <TableCell className="text-xs font-bold text-[#1d1d1f]">
                      {formatCurrency(tx.amount)}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-[#0071e3]">
                      {tx.matched_invoice_number || '—'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          tx.status === 'matched'
                            ? 'success'
                            : tx.status === 'unmatched'
                            ? 'warning'
                            : 'danger'
                        }
                        size="sm"
                      >
                        {tx.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {tx.status === 'unmatched' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedTxForMatch(tx.id)}
                        >
                          Manual Match
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            )}
          </Table>
        </div>
      )}

      {/* CSV Upload Modal */}
      {uploadModalOpen && (
        <Modal
          isOpen={uploadModalOpen}
          onClose={() => setUploadModalOpen(false)}
          title="Upload Bank Statement CSV"
          description="Drag and drop your bank or payment processor export to run automated reconciliation"
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-black/[0.1] p-8 text-center bg-[#f5f5f7]">
              <Upload className="h-10 w-10 text-[#0071e3] mb-2" />
              <p className="text-xs font-semibold text-[#1d1d1f]">
                bank_statement_november_2026.csv
              </p>
              <p className="text-[11px] text-[#6e6e73] mt-1">Ready for parsing (32 rows detected)</p>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-black/[0.06]">
              <Button variant="outline" onClick={() => setUploadModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => uploadCsvMutation.mutate()}
                isLoading={uploadCsvMutation.isPending}
                leftIcon={<Sparkles className="h-4 w-4" />}
              >
                Start Reconciliation
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Manual Match Invoice Selector Modal */}
      {selectedTxForMatch && (
        <Modal
          isOpen={!!selectedTxForMatch}
          onClose={() => setSelectedTxForMatch(null)}
          title="Manual Invoice Reconciliation"
          description="Select an open invoice to bind this unmatched transaction"
          maxWidth="lg"
        >
          <div className="space-y-3">
            <p className="text-xs font-semibold text-[#6e6e73]">
              Select Outstanding Customer Invoice:
            </p>
            <div className="divide-y divide-black/[0.05] border border-black/[0.08] rounded-2xl overflow-hidden text-xs max-h-60 overflow-y-auto">
              {invoices
                .filter((i) => i.balance_due > 0)
                .map((inv) => (
                  <div
                    key={inv.id}
                    className="flex items-center justify-between p-3 hover:bg-black/[0.02] cursor-pointer"
                    onClick={() =>
                      matchTxMutation.mutate({ txId: selectedTxForMatch, invoiceId: inv.id })
                    }
                  >
                    <div>
                      <p className="font-semibold text-[#1d1d1f]">{inv.invoice_number}</p>
                      <p className="text-[11px] text-[#6e6e73]">{inv.customer?.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-rose-700">{formatCurrency(inv.balance_due)}</p>
                      <span className="text-[10px] text-[#0071e3] font-medium">Click to bind</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
