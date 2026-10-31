import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Clock,
  ArrowRight,
  ExternalLink,
  Shield,
  Eye,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { verificationService } from '../../services/verificationService';
import { VerificationContract } from '../../types';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';

export const VerificationList: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedVerification, setSelectedVerification] = useState<VerificationContract | null>(null);

  const { data: verifications = [], isLoading } = useQuery({
    queryKey: ['verifications'],
    queryFn: () => verificationService.getVerifications(),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => verificationService.approveCredit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verifications'] });
      queryClient.invalidateQueries({ queryKey: ['digitalTwin'] });
      setSelectedVerification(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => verificationService.rejectCredit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verifications'] });
      setSelectedVerification(null);
    },
  });

  const verifiedCount = verifications.filter((v) => v.status === 'verified').length;
  const discrepancyCount = verifications.filter((v) => v.discrepancy_detected).length;
  const totalCredits = verifications.reduce((sum, v) => sum + (v.proposed_credit || 0), 0);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Contract-to-Bill Value Verification
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Compare contracted SLA commitments against actual operational telemetry and adjudicate proposed service credits
          </p>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Verified Compliant Contracts</span>
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-600">{verifiedCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">100% SLA delivery match</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Discrepancies Detected</span>
            <AlertTriangle className="h-4 w-4 text-rose-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-rose-600">{discrepancyCount}</p>
          <p className="text-[11px] text-rose-500 mt-1">Pending review & billing adjustment</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Proposed SLA Credits</span>
            <Clock className="h-4 w-4 text-brand-600" />
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(totalCredits)}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Protects customer billing trust</p>
        </div>
      </div>

      {/* Verification Contracts Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Contract #</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Service Name</TableHead>
            <TableHead>Contract Commitment (SLA)</TableHead>
            <TableHead>Actual Recorded Telemetry</TableHead>
            <TableHead>Proposed Credit</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={8} rowsCount={3} />
        ) : verifications.length === 0 ? (
          <TableEmpty
            title="No contract verifications found"
            description="Active subscription contracts will automatically stream telemetry here for SLA reconciliation."
            colSpan={8}
          />
        ) : (
          <TableBody>
            {verifications.map((v) => {
              const badge = getStatusBadgeVariant(v.status);
              return (
                <TableRow key={v.id}>
                  <TableCell className="font-mono text-xs font-semibold text-slate-900 dark:text-white">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-brand-600" />
                      {v.contract_number}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs font-medium">
                    {v.customer?.name || 'Client Entity'}
                  </TableCell>
                  <TableCell className="text-xs text-slate-700 dark:text-slate-300">
                    {v.service_name}
                  </TableCell>
                  <TableCell className="text-xs max-w-xs font-mono text-slate-600 dark:text-slate-400">
                    {v.contract_sla}
                  </TableCell>
                  <TableCell className="text-xs max-w-xs">
                    <span
                      className={
                        v.discrepancy_detected
                          ? 'text-rose-600 font-semibold'
                          : 'text-emerald-600 font-semibold'
                      }
                    >
                      {v.actual_recorded_delivery}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                    {v.proposed_credit > 0 ? (
                      <span className="text-rose-600">
                        {formatCurrency(v.proposed_credit, v.currency)}
                      </span>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        v.status === 'verified'
                          ? 'success'
                          : v.status === 'discrepancy_detected' || v.status === 'pending_review'
                          ? 'warning'
                          : v.status === 'approved'
                          ? 'info'
                          : 'danger'
                      }
                      size="sm"
                    >
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedVerification(v)}
                      leftIcon={<Eye className="h-3.5 w-3.5" />}
                    >
                      Review
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        )}
      </Table>

      {/* Comparison & Adjudication Modal */}
      {selectedVerification && (
        <Modal
          isOpen={!!selectedVerification}
          onClose={() => setSelectedVerification(null)}
          title={`Contract Adjudication: ${selectedVerification.contract_number}`}
          description={`Customer: ${selectedVerification.customer?.name} • Service: ${selectedVerification.service_name}`}
          maxWidth="2xl"
        >
          <div className="space-y-6">
            {/* Status Banner */}
            <div className="flex items-center justify-between rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
              <div>
                <span className="text-xs text-slate-500">Verification Status</span>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedVerification.status === 'verified'
                        ? 'success'
                        : selectedVerification.discrepancy_detected
                        ? 'danger'
                        : 'default'
                    }
                    size="md"
                  >
                    {selectedVerification.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500">Proposed Service Credit</span>
                <p className="text-xl font-bold text-rose-600">
                  {formatCurrency(selectedVerification.proposed_credit, selectedVerification.currency)}
                </p>
              </div>
            </div>

            {/* Expected vs Actual Side-by-Side Comparison */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-200 bg-emerald-50/30 p-4 dark:border-slate-800 dark:bg-emerald-950/20">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                  Contractual Expectation
                </span>
                <p className="mt-2 text-xs font-semibold text-slate-900 dark:text-white">
                  {selectedVerification.contract_sla}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  Target: {selectedVerification.expected_service_delivery}
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-rose-50/30 p-4 dark:border-slate-800 dark:bg-rose-950/20">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-800 dark:text-rose-300">
                  Actual Recorded Telemetry
                </span>
                <p className="mt-2 text-xs font-semibold text-rose-900 dark:text-rose-200">
                  {selectedVerification.actual_recorded_delivery}
                </p>
                {selectedVerification.discrepancy_details && (
                  <p className="mt-1 text-[11px] text-rose-600 dark:text-rose-400">
                    Delta: {selectedVerification.discrepancy_details}
                  </p>
                )}
              </div>
            </div>

            {/* Evidence References */}
            <div className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Evidence References & Audit Trail Hashes
              </span>
              <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 space-y-1.5">
                {selectedVerification.evidence_references.map((ref, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-600 dark:text-slate-300">{ref}</span>
                    <span className="inline-flex items-center gap-1 text-[11px] text-brand-600 font-medium cursor-pointer hover:underline">
                      Inspect Telemetry <ExternalLink className="h-3 w-3" />
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Adjudication Action Buttons */}
            {selectedVerification.discrepancy_detected && selectedVerification.status !== 'approved' && selectedVerification.status !== 'rejected' && (
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button
                  variant="outline"
                  onClick={() => rejectMutation.mutate(selectedVerification.id)}
                  isLoading={rejectMutation.isPending}
                  leftIcon={<XCircle className="h-4 w-4 text-rose-600" />}
                >
                  Reject Credit Proposal
                </Button>
                <Button
                  onClick={() => approveMutation.mutate(selectedVerification.id)}
                  isLoading={approveMutation.isPending}
                  leftIcon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                >
                  Approve SLA Credit ({formatCurrency(selectedVerification.proposed_credit)})
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
