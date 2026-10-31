import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Plus, CheckCircle2, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { invoiceService } from '../../services/invoiceService';
import { CustomerDispute } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

export const CustomerDisputes: React.FC = () => {
  const [isFilingOpen, setIsFilingOpen] = useState(false);
  const [disputes, setDisputes] = useState<CustomerDispute[]>([
    {
      id: 'disp-001',
      dispute_number: 'DISP-2026-081',
      customer_id: 'cust-001',
      invoice_number: 'INV-2026-1044',
      reason: 'SLA Downtime Credit Reconciliation',
      description: 'Requesting 10% credit adjustment for Oct 12 network maintenance latency window.',
      amount_disputed: 249.9,
      status: 'under_review',
      created_at: '2026-10-21T09:00:00Z',
    },
  ]);

  const [selectedInvoice, setSelectedInvoice] = useState('');
  const [reason, setReason] = useState('');
  const [amount, setAmount] = useState(150);
  const [description, setDescription] = useState('');

  const { data: invoices = [] } = useQuery({
    queryKey: ['customerInvoices'],
    queryFn: () => invoiceService.getInvoices(),
  });

  const handleFileDispute = () => {
    const newDispute: CustomerDispute = {
      id: 'disp-' + Date.now(),
      dispute_number: `DISP-2026-${Math.floor(100 + Math.random() * 900)}`,
      customer_id: 'cust-001',
      invoice_number: selectedInvoice || 'INV-2026-1060',
      reason,
      description,
      amount_disputed: amount,
      status: 'submitted',
      created_at: new Date().toISOString(),
    };
    setDisputes([newDispute, ...disputes]);
    setIsFilingOpen(false);
    setReason('');
    setDescription('');
  };

  return (
    <div className="space-y-6 text-left">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Billing Inquiries & Disputes
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Submit questions regarding invoice line items, request SLA adjustments, and track resolution status
          </p>
        </div>
        <Button onClick={() => setIsFilingOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Raise Dispute
        </Button>
      </div>

      <div className="space-y-4">
        {disputes.map((d) => (
          <Card key={d.id}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <h4 className="font-bold text-xs text-slate-900 dark:text-white">
                    {d.dispute_number}: {d.reason}
                  </h4>
                </div>
                <Badge variant={d.status === 'resolved' ? 'success' : 'warning'} size="sm">
                  {d.status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                {d.description}
              </p>

              <div className="mt-3 flex items-center justify-between pt-2 border-t text-[11px] text-slate-400">
                <span>Invoice: <strong className="text-brand-600">{d.invoice_number}</strong></span>
                <span>Amount: <strong className="text-slate-900 dark:text-white">{formatCurrency(d.amount_disputed)}</strong></span>
                <span>Submitted: {formatDate(d.created_at)}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Modal */}
      {isFilingOpen && (
        <Modal
          isOpen={isFilingOpen}
          onClose={() => setIsFilingOpen(false)}
          title="Raise Billing Dispute"
          description="Submit an inquiry to the finance & engineering verification team"
          maxWidth="md"
        >
          <div className="space-y-4">
            <Select
              label="Select Invoice"
              options={invoices.map((i) => ({ label: `${i.invoice_number} ($${i.total_amount})`, value: i.invoice_number }))}
              value={selectedInvoice}
              onChange={(e) => setSelectedInvoice(e.target.value)}
            />
            <Input
              label="Dispute Reason"
              placeholder="e.g. Downtime SLA Breach"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Input
              label="Disputed Amount ($)"
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
            />
            <Input
              label="Explanation & Timestamp Evidence"
              placeholder="Describe the incident or calculation discrepancy..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setIsFilingOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleFileDispute} disabled={!reason}>
                Submit Dispute
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
