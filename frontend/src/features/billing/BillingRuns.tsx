import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Zap, Play, CheckCircle2, Clock, Terminal } from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { billingService } from '../../services/billingService';
import { subscriptionService } from '../../services/subscriptionService';
import { formatDateTime } from '../../utils';

export const BillingRuns: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedLogs, setSelectedLogs] = useState<string[] | null>(null);

  const { data: runs = [], isLoading: isRunsLoading } = useQuery({
    queryKey: ['billingRuns'],
    queryFn: () => billingService.getBillingRuns(),
  });

  const { data: subscriptions = [] } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionService.getSubscriptions(),
  });

  const activeDueSubs = subscriptions.filter((s) => s.status === 'active');

  const executeMutation = useMutation({
    mutationFn: () => billingService.executeBillingRun(),
    onSuccess: (newRun) => {
      queryClient.invalidateQueries({ queryKey: ['billingRuns'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardMetrics'] });
      setSelectedLogs(newRun.logs);
    },
  });

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Invoices', path: '/admin/invoices' },
          { label: 'Payments & Reconciliation', path: '/admin/payments' },
          { label: 'Automated Billing Runs', path: '/admin/billing', badge: `${runs.length}` },
          { label: 'Discount Rules', path: '/admin/discounts' },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Automated Billing Engine & Execution Runs
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Trigger recurring invoice generation runs, view batch logs, and inspect due subscriptions
          </p>
        </div>
        <Button
          onClick={() => executeMutation.mutate()}
          isLoading={executeMutation.isPending}
          leftIcon={<Play className="h-3.5 w-3.5" />}
        >
          Execute Billing Run Now
        </Button>
      </div>

      {/* Due Subscriptions Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Subscriptions Due for Billing</span>
            <Zap className="h-4 w-4 text-[#0071e3]" />
          </div>
          <p className="mt-2 text-2xl font-bold text-[#1d1d1f]">
            {activeDueSubs.length}
          </p>
          <p className="text-[11px] text-[#6e6e73] mt-1">Ready for automated invoicing</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Last Run Success Rate</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-700">98.6%</p>
          <p className="text-[11px] text-emerald-700 mt-1 font-medium">Zero critical ledger drops</p>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs text-[#6e6e73]">
            <span>Total Completed Runs</span>
            <Clock className="h-4 w-4 text-[#0071e3]" />
          </div>
          <p className="mt-2 text-2xl font-bold text-[#1d1d1f]">{runs.length}</p>
          <p className="text-[11px] text-[#6e6e73] mt-1">Immutable audit logging</p>
        </div>
      </div>

      {/* Execution Logs Drawer if available */}
      {selectedLogs && (
        <Card className="border border-black/[0.1] bg-[#1d1d1f] text-slate-100 font-mono text-xs shadow-xl rounded-2xl">
          <CardHeader className="border-b border-white/[0.08] pb-3 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-[#0071e3]" />
              <CardTitle className="text-white text-xs">Billing Daemon Live Execution Log</CardTitle>
            </div>
            <button
              onClick={() => setSelectedLogs(null)}
              className="text-slate-400 hover:text-white text-[11px]"
            >
              Close
            </button>
          </CardHeader>
          <CardContent className="space-y-1 py-3">
            {selectedLogs.map((log, i) => (
              <p key={i} className="text-emerald-400">
                {log}
              </p>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Historical Billing Runs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Historical Billing Execution Cycles</CardTitle>
          <CardDescription>Logs, generated invoices count, and exception metrics</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run Number</TableHead>
                <TableHead>Execution Date</TableHead>
                <TableHead>Due Subscriptions</TableHead>
                <TableHead>Invoices Generated</TableHead>
                <TableHead>Exceptions</TableHead>
                <TableHead>Execution Status</TableHead>
                <TableHead className="text-right">Logs</TableHead>
              </TableRow>
            </TableHeader>
            {isRunsLoading ? (
              <TableLoading columnsCount={7} rowsCount={3} />
            ) : runs.length === 0 ? (
              <TableEmpty
                title="No billing runs yet"
                description="Run the billing engine to process active subscriptions and generate period invoices."
                actionText="Execute Run"
                onAction={() => executeMutation.mutate()}
                colSpan={7}
              />
            ) : (
              <TableBody>
                {runs.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-mono text-xs font-semibold text-[#0071e3]">
                      {r.run_number}
                    </TableCell>
                    <TableCell className="text-xs text-[#6e6e73]">
                      {formatDateTime(r.execution_date)}
                    </TableCell>
                    <TableCell className="text-xs font-medium text-[#1d1d1f]">
                      {r.total_due_subscriptions}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-emerald-700">
                      {r.successful_invoices}
                    </TableCell>
                    <TableCell className="text-xs text-rose-700 font-semibold">
                      {r.failed_items}
                    </TableCell>
                    <TableCell>
                      <Badge variant={r.status === 'completed' ? 'success' : 'warning'} size="sm">
                        {r.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedLogs(r.logs)}
                        leftIcon={<Terminal className="h-3 w-3" />}
                      >
                        Inspect
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            )}
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};
