import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CreditCard,
  Plus,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  DollarSign,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Tabs } from '../../components/common/Tabs';
import { paymentService } from '../../services/paymentService';
import { invoiceService } from '../../services/invoiceService';
import { Payment } from '../../types';
import { formatCurrency, formatDateTime, formatDate, getStatusBadgeVariant } from '../../utils';

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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Payments & Bank Reconciliation
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Track customer payments, Stripe & ACH transactions, and automated statement reconciliation
          </p>
        </div>

        {activeTab === 'reconciliation' && (
          <Button
            onClick={() => setUploadModalOpen(true)}
            leftIcon={<Upload className="h-4 w-4" />}
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
                    <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        <CreditCard className="h-4 w-4 text-brand-600" />
                        {p.payment_number}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs font-mono font-medium text-brand-600">
                      {p.invoice_number || 'INV-SETTLE'}
                    </TableCell>
                    <TableCell className="text-xs">
                      {p.customer?.name || 'Customer Account'}
                    </TableCell>
                    <TableCell className="text-xs capitalize text-slate-600 dark:text-slate-300">
                      {p.payment_method.replace('_', ' ')}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-slate-500">
                      {p.reference}
                    </TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {formatDateTime(p.payment_date)}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
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
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Transactions</span>
              <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                {reconciliation?.total_records || 0}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">{reconciliation?.file_name}</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Auto-Matched</span>
              <p className="mt-1 text-2xl font-bold text-emerald-600">
                {reconciliation?.matched_count || 0}
              </p>
              <p className="text-[11px] text-emerald-600 mt-0.5">High confidence &gt; 98%</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Unmatched (Review)</span>
              <p className="mt-1 text-2xl font-bold text-amber-600">
                {reconciliation?.unmatched_count || 0}
              </p>
              <p className="text-[11px] text-amber-600 mt-0.5">Requires manual attribution</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Potential Duplicates</span>
              <p className="mt-1 text-2xl font-bold text-rose-600">
                {reconciliation?.duplicate_count || 0}
              </p>
              <p className="text-[11px] text-rose-600 mt-0.5">Flagged for deduplication</p>
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
                    <TableCell className="text-xs text-slate-500">{tx.date}</TableCell>
                    <TableCell className="text-xs font-semibold text-slate-900 dark:text-white">
                      {tx.description}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-slate-500">{tx.reference}</TableCell>
                    <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                      {formatCurrency(tx.amount)}
                    </TableCell>
                    <TableCell className="text-xs font-mono text-brand-600">
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
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 p-8 text-center dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
              <Upload className="h-10 w-10 text-brand-600 mb-2" />
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                bank_statement_november_2026.csv
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Ready for parsing (32 rows detected)</p>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
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
            <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
              Select Outstanding Customer Invoice:
            </p>
            <div className="divide-y divide-slate-100 dark:divide-slate-800 border rounded-xl overflow-hidden text-xs max-h-60 overflow-y-auto">
              {invoices
                .filter((i) => i.balance_due > 0)
                .map((inv) => (
                  <div
                    key={inv.id}
                    className="flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
                    onClick={() =>
                      matchTxMutation.mutate({ txId: selectedTxForMatch, invoiceId: inv.id })
                    }
                  >
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">{inv.invoice_number}</p>
                      <p className="text-[11px] text-slate-500">{inv.customer?.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-rose-600">{formatCurrency(inv.balance_due)}</p>
                      <span className="text-[10px] text-brand-600 font-medium">Click to bind</span>
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
