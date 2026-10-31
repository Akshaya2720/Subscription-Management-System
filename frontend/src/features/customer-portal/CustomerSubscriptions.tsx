import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Repeat, Pause, Play, CheckCircle2, Shield } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading } from '../../components/common/Table';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { subscriptionService } from '../../services/subscriptionService';
import { formatCurrency, formatDate } from '../../utils';

export const CustomerSubscriptions: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: subscriptions = [], isLoading } = useQuery({
    queryKey: ['customerSubscriptions'],
    queryFn: () => subscriptionService.getSubscriptions(),
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.pauseSubscription(id, 'Client initiated pause from portal'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['customerSubscriptions'] }),
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.resumeSubscription(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['customerSubscriptions'] }),
  });

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          My Subscriptions & Service Tiers
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Review your enrolled plans, billing frequencies, renewal dates, and manage operational pause controls
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Subscription #</TableHead>
            <TableHead>Plan Tier</TableHead>
            <TableHead>Contracted Rate</TableHead>
            <TableHead>Cadence</TableHead>
            <TableHead>Next Billing Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        {isLoading ? (
          <TableLoading columnsCount={7} rowsCount={2} />
        ) : (
          <TableBody>
            {subscriptions.map((s) => (
              <TableRow key={s.id}>
                <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                  <div className="flex items-center gap-2">
                    <Repeat className="h-4 w-4 text-brand-600" />
                    {s.subscription_number}
                  </div>
                </TableCell>
                <TableCell className="text-xs">
                  {s.plan?.name || 'Cloud Infrastructure Tier'}
                </TableCell>
                <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
                  {formatCurrency(s.contracted_price, s.currency)}
                </TableCell>
                <TableCell className="text-xs capitalize">{s.billing_frequency}</TableCell>
                <TableCell className="text-xs text-slate-500">
                  {formatDate(s.next_billing_date)}
                </TableCell>
                <TableCell>
                  <Badge variant={s.status === 'active' ? 'success' : s.status === 'paused' ? 'warning' : 'default'} size="sm">
                    {s.status.toUpperCase()}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {s.status === 'active' ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => pauseMutation.mutate(s.id)}
                      isLoading={pauseMutation.isPending}
                      leftIcon={<Pause className="h-3 w-3" />}
                    >
                      Request Pause
                    </Button>
                  ) : s.status === 'paused' ? (
                    <Button
                      size="sm"
                      onClick={() => resumeMutation.mutate(s.id)}
                      isLoading={resumeMutation.isPending}
                      leftIcon={<Play className="h-3 w-3" />}
                    >
                      Resume Service
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        )}
      </Table>
    </div>
  );
};
