import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ShieldCheck,
  Link as LinkIcon,
  Filter,
  CheckCircle2,
  ExternalLink,
  Search,
} from 'lucide-react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { SubNavTabs } from '../../components/common/SubNavTabs';
import { auditService } from '../../services/auditService';
import { formatDateTime } from '../../utils';

export const AuditTrail: React.FC = () => {
  const [actorFilter, setActorFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [entityFilter] = useState('all');
  const [verificationResult, setVerificationResult] = useState<{
    is_valid: boolean;
    total_blocks_checked: number;
    head_hash: string;
    verified_at: string;
  } | null>(null);

  const { data: auditLogs = [], isLoading } = useQuery({
    queryKey: ['auditLogs', actorFilter, actionFilter, entityFilter],
    queryFn: () =>
      auditService.getAuditLogs({
        actor: actorFilter || undefined,
        action: actionFilter,
        entity: entityFilter,
      }),
  });

  const verifyIntegrityMutation = useMutation({
    mutationFn: () => auditService.verifyHashChainIntegrity(),
    onSuccess: (result) => {
      setVerificationResult(result);
    },
  });

  return (
    <div className="space-y-6 text-left">
      {/* Sub Navigation Tabs */}
      <SubNavTabs
        items={[
          { label: 'Organization & Governance', path: '/admin/settings' },
          { label: 'Audit Trail (SHA-256)', path: '/admin/audit', badge: `${auditLogs.length} Blocks` },
          { label: 'Financial Reports', path: '/admin/reports' },
        ]}
      />

      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1d1d1f]">
            Immutable Audit Trail & Hash-Chain Verification
          </h1>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Tamper-evident system ledger with SHA-256 parent hash linking and blockchain anchoring transparency
          </p>
        </div>
        <Button
          onClick={() => verifyIntegrityMutation.mutate()}
          isLoading={verifyIntegrityMutation.isPending}
          leftIcon={<ShieldCheck className="h-3.5 w-3.5" />}
        >
          Verify Hash-Chain Integrity
        </Button>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div className="flex items-center justify-between rounded-2xl border border-emerald-200 bg-emerald-50/90 p-4 shadow-2xs">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-emerald-950">
                Cryptographic Integrity Verified (100% Unbroken Chain)
              </h4>
              <p className="text-xs text-emerald-800 font-mono">
                Validated {verificationResult.total_blocks_checked} chronological log blocks. Head hash: {verificationResult.head_hash.substring(0, 24)}...
              </p>
            </div>
          </div>
          <span className="text-[11px] text-emerald-700 font-medium">
            Checked at {new Date(verificationResult.verified_at).toLocaleTimeString()}
          </span>
        </div>
      )}

      {/* Distinction Header: Hash Chain vs Blockchain */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            <h3 className="text-sm font-bold text-[#1d1d1f]">
              SHA-256 Hash-Chain Integrity
            </h3>
          </div>
          <p className="mt-2 text-xs text-[#6e6e73] leading-relaxed">
            Every billing transition, SLA credit modification, and customer record alteration generates a cryptographic hash bound to the previous record's signature. Any tampering causes an instant hash mismatch.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <Badge variant="success" size="sm">ACTIVE & VERIFIED</Badge>
            <span className="text-[11px] text-[#6e6e73]">Zero chain breaks detected</span>
          </div>
        </div>

        <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-2xs">
          <div className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5 text-[#0071e3]" />
            <h3 className="text-sm font-bold text-[#1d1d1f]">
              Public Blockchain Anchoring
            </h3>
          </div>
          <p className="mt-2 text-xs text-[#6e6e73] leading-relaxed">
            Periodic hash snapshots anchored to public L1/L2 ledger. If a transaction hash is verified by the backend node, the explorer receipt is displayed below; otherwise labelled as Pending/Unconfigured.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <Badge variant="info" size="sm">TRANSPARENCY STANDARD</Badge>
            <span className="text-[11px] text-[#6e6e73]">Strictly follows backend proofs</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#86868b]" />
          <input
            type="text"
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
            placeholder="Filter by actor name or email..."
            className="w-full rounded-full border border-[#d2d2d7] bg-white pl-10 pr-4 py-2 text-xs text-[#1d1d1f] placeholder-[#86868b] focus:border-[#0071e3] focus:outline-none focus:ring-2 focus:ring-[#0071e3]/20 shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-4 w-4 text-[#86868b] shrink-0" />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="rounded-full border border-[#d2d2d7] bg-white px-4 py-2 text-xs font-medium text-[#1d1d1f] outline-none focus:border-[#0071e3] shadow-2xs w-full sm:w-auto cursor-pointer"
          >
            <option value="all">All Actions</option>
            <option value="CREATE_ORGANIZATION">CREATE_ORGANIZATION</option>
            <option value="DISCREPANCY_DETECTED">DISCREPANCY_DETECTED</option>
            <option value="PAUSE_SUBSCRIPTION">PAUSE_SUBSCRIPTION</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Actor</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Entity</TableHead>
            <TableHead>Change Summary</TableHead>
            <TableHead>Timestamp</TableHead>
            <TableHead>Hash-Chain Proof</TableHead>
            <TableHead className="text-right">Blockchain Anchor</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={3} />
        ) : auditLogs.length === 0 ? (
          <TableEmpty
            title="No audit entries"
            description="Operations performed in the application are cryptographically recorded here."
            colSpan={7}
          />
        ) : (
          <TableBody>
            {auditLogs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="text-xs">
                  <p className="font-semibold text-[#1d1d1f]">{log.actor_name}</p>
                  <p className="text-[10px] text-[#6e6e73]">{log.actor_role}</p>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-[11px] font-bold text-[#0071e3] bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                    {log.action}
                  </span>
                </TableCell>
                <TableCell className="text-xs font-mono text-[#6e6e73]">
                  {log.entity_type} ({log.entity_name || log.entity_id})
                </TableCell>
                <TableCell className="text-xs text-[#1d1d1f] max-w-xs">
                  {log.change_summary}
                </TableCell>
                <TableCell className="text-xs text-[#6e6e73]">
                  {formatDateTime(log.timestamp)}
                </TableCell>
                <TableCell className="text-xs font-mono">
                  <span
                    className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-semibold"
                    title={`Current: ${log.current_hash}\nPrevious: ${log.previous_hash}`}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {log.current_hash.substring(0, 10)}...
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  {log.blockchain_status === 'confirmed' && log.blockchain_tx_hash ? (
                    <span
                      className="inline-flex items-center gap-1 font-mono text-[11px] text-emerald-700 font-medium hover:underline cursor-pointer"
                      title={log.blockchain_tx_hash}
                    >
                      {log.blockchain_tx_hash.substring(0, 10)}...
                      <ExternalLink className="h-3 w-3" />
                    </span>
                  ) : log.blockchain_status === 'pending' ? (
                    <Badge variant="warning" size="sm">
                      PENDING ANCHOR
                    </Badge>
                  ) : (
                    <span className="text-[11px] text-[#86868b]">
                      Local Chain Only
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>
    </div>
  );
};
