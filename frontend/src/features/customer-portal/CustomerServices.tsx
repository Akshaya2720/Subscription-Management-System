import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { verificationService } from '../../services/verificationService';
import { formatDate } from '../../utils';

export const CustomerServices: React.FC = () => {
  const { data: verifications = [] } = useQuery({
    queryKey: ['customerServices'],
    queryFn: () => verificationService.getVerifications(),
  });

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Delivered Services & Verified Value
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Cryptographically recorded SLA compliance, cluster uptime telemetry, and contract delivery guarantees
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-5">
          <span className="text-xs font-semibold uppercase text-slate-500">Uptime Compliance</span>
          <p className="mt-2 text-2xl font-bold text-emerald-600">99.98%</p>
          <p className="text-xs text-slate-400 mt-1">Contract SLA target: 99.9%</p>
        </Card>

        <Card className="p-5">
          <span className="text-xs font-semibold uppercase text-slate-500">Service Hours Logged</span>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">741.2 hrs</p>
          <p className="text-xs text-slate-400 mt-1">Period total: 744 operating hours</p>
        </Card>

        <Card className="p-5">
          <span className="text-xs font-semibold uppercase text-slate-500">Verified SLA Audits</span>
          <p className="mt-2 text-2xl font-bold text-brand-600">{verifications.length}</p>
          <p className="text-xs text-slate-400 mt-1">Zero unacknowledged disputes</p>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Verified Service Delivery History</CardTitle>
          <CardDescription>Continuous contract-to-bill telemetry comparisons</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {verifications.map((v) => (
              <div key={v.id} className="p-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    <p className="font-semibold text-slate-900 dark:text-white">{v.service_name}</p>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">SLA Target: {v.contract_sla}</p>
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">
                    Actual: {v.actual_recorded_delivery}
                  </p>
                </div>
                <div className="text-right">
                  <Badge variant={v.discrepancy_detected ? 'warning' : 'success'}>
                    {v.discrepancy_detected ? 'ADJUSTMENT PENDING' : 'VERIFIED COMPLIANT'}
                  </Badge>
                  <p className="text-[10px] text-slate-400 mt-1">{formatDate(v.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
