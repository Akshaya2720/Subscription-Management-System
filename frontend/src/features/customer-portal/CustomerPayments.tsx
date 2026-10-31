import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CreditCard } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading } from '../../components/common/Table';
import { Badge } from '../../components/common/Badge';
import { paymentService } from '../../services/paymentService';
import { formatCurrency, formatDateTime } from '../../utils';

export const CustomerPayments: React.FC = () => {
  const { data: payments = [], isLoading } = useQuery({
    queryKey: ['customerPayments'],
    queryFn: () => paymentService.getPayments(),
  });

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
          Payment History & Settlement Receipts
        </h1>
        <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
          Complete log of processed credit card charges, wire transfers, and gateway confirmations
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Payment #</TableHead>
            <TableHead>Linked Invoice</TableHead>
            <TableHead>Payment Method</TableHead>
            <TableHead>Gateway Reference</TableHead>
            <TableHead>Date & Time</TableHead>
            <TableHead>Amount Paid</TableHead>
            <TableHead className="text-right">Status</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={2} />
        ) : (
          <TableBody>
            {payments.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-semibold text-xs text-[#0071e3]">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-[#0071e3]" />
                    {p.payment_number}
                  </div>
                </TableCell>
                <TableCell className="text-xs font-mono font-medium text-[#0071e3]">
                  {p.invoice_number || 'INV-AUTO'}
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
                <TableCell className="text-right">
                  <Badge variant="success" size="sm">
                    {p.status.toUpperCase()}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>
    </div>
  );
};
