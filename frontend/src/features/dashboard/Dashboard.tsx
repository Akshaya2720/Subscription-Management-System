import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Repeat,
  DollarSign,
  AlertCircle,
  Clock,
  ShieldAlert,
  ArrowUpRight,
  Filter,
  Plus,
  ShieldCheck,
  Sparkles,
  Receipt,
  Activity,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { StatCard } from '../../components/common/StatCard';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableLoadingState,
  TableEmptyState,
} from '../../components/common/Table';
import { dashboardService } from '../../services/dashboardService';
import { subscriptionService } from '../../services/subscriptionService';
import { invoiceService } from '../../services/invoiceService';
import { verificationService } from '../../services/verificationService';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';
import { Link, useNavigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [dateRange, setDateRange] = useState('30d');
  const [statusFilter, setStatusFilter] = useState('all');

  // Fetch live metrics
  const { data: metrics, isLoading: isMetricsLoading } = useQuery({
    queryKey: ['dashboardMetrics', dateRange],
    queryFn: () => dashboardService.getMetrics(dateRange),
  });

  // Fetch recent subscriptions
  const { data: subscriptions = [], isLoading: isSubsLoading } = useQuery({
    queryKey: ['subscriptions', statusFilter],
    queryFn: () => subscriptionService.getSubscriptions(undefined, statusFilter),
  });

  // Fetch recent invoices
  const { data: invoices = [], isLoading: isInvoicesLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => invoiceService.getInvoices(),
  });

  // Fetch verification alerts
  const { data: verifications = [] } = useQuery({
    queryKey: ['verifications'],
    queryFn: () => verificationService.getVerifications(),
  });

  const overdueInvoices = invoices.filter((i) => i.status === 'overdue');
  const verificationAlerts = verifications.filter((v) => v.discrepancy_detected);

  return (
    <div className="space-y-6 text-left">
      {/* Supaste Floating Category Shelf Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar select-none">
        <button
          onClick={() => navigate('/admin/subscriptions')}
          className="flex items-center gap-2 rounded-full bg-blue-600/20 border border-blue-500/35 px-4 py-1.5 text-xs font-semibold text-blue-300 shadow-glow-blue backdrop-blur-md transition-all hover:bg-blue-600/30"
        >
          <Repeat className="h-3.5 w-3.5" />
          <span>Active Subscriptions ({metrics?.active_subscriptions || 2})</span>
        </button>

        <button
          onClick={() => navigate('/admin/verification')}
          className="flex items-center gap-2 rounded-full bg-white/[0.05] border border-white/[0.09] px-4 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.09] backdrop-blur-md transition-all"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>Hash-Chain Verified</span>
        </button>

        <button
          onClick={() => navigate('/admin/invoices')}
          className="flex items-center gap-2 rounded-full bg-white/[0.05] border border-white/[0.09] px-4 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/[0.09] backdrop-blur-md transition-all"
        >
          <Receipt className="h-3.5 w-3.5 text-cyan-400" />
          <span>Automated Billing Ledger</span>
        </button>

        {verificationAlerts.length > 0 && (
          <button
            onClick={() => navigate('/admin/verification')}
            className="flex items-center gap-2 rounded-full bg-rose-500/15 border border-rose-500/30 px-4 py-1.5 text-xs font-semibold text-rose-300 shadow-sm backdrop-blur-md hover:bg-rose-500/25 transition-all"
          >
            <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
            <span>1 SLA Telemetry Discrepancy</span>
          </button>
        )}
      </div>

      {/* Hero Header & Quick Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              Platform Overview
            </h1>
            <span className="rounded-full bg-blue-500/15 border border-blue-500/30 px-2.5 py-0.5 text-[10px] font-mono font-medium text-blue-300">
              macOS v2.4
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Contract-to-bill verification telemetry, recurring revenue velocity, and automated settlements
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 rounded-full border border-white/[0.1] bg-white/[0.05] px-3.5 py-1.5 text-xs backdrop-blur-md">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer"
            >
              <option value="7d" className="bg-[#0c1220]">Last 7 Days</option>
              <option value="30d" className="bg-[#0c1220]">Last 30 Days</option>
              <option value="90d" className="bg-[#0c1220]">Last 90 Days</option>
              <option value="1y" className="bg-[#0c1220]">This Year</option>
            </select>
          </div>

          <Button
            size="sm"
            onClick={() => navigate('/admin/subscriptions')}
            leftIcon={<Plus className="h-3.5 w-3.5" />}
          >
            New Subscription
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => navigate('/admin/verification')}
            leftIcon={<ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />}
          >
            SLA Verification
          </Button>
        </div>
      </div>

      {/* Supaste Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
        <StatCard
          title="Active Subs"
          value={metrics?.active_subscriptions || 0}
          change={metrics?.active_subscriptions_change}
          icon={<Repeat className="h-4 w-4" />}
          iconBg="bg-blue-500/15 border border-blue-500/25"
          iconColor="text-blue-400"
        />

        <StatCard
          title="Revenue Recv"
          value={formatCurrency(metrics?.revenue_received)}
          change={metrics?.revenue_change}
          icon={<DollarSign className="h-4 w-4" />}
          iconBg="bg-emerald-500/15 border border-emerald-500/25"
          iconColor="text-emerald-400"
        />

        <StatCard
          title="Outstanding"
          value={formatCurrency(metrics?.outstanding_amount)}
          change={metrics?.outstanding_change}
          icon={<Clock className="h-4 w-4" />}
          iconBg="bg-amber-500/15 border border-amber-500/25"
          iconColor="text-amber-400"
        />

        <StatCard
          title="Overdue"
          value={metrics?.overdue_invoices || 0}
          badge={metrics?.overdue_invoices ? 'Action Required' : '0 Alerts'}
          icon={<AlertCircle className="h-4 w-4" />}
          iconBg="bg-rose-500/15 border border-rose-500/25"
          iconColor="text-rose-400"
        />

        <StatCard
          title="Accounts"
          value={metrics?.total_customers || 0}
          change={metrics?.total_customers_change}
          icon={<Users className="h-4 w-4" />}
          iconBg="bg-cyan-500/15 border border-cyan-500/25"
          iconColor="text-cyan-400"
        />

        <StatCard
          title="Renewals"
          value={metrics?.upcoming_renewals || 0}
          subtitle="Next 30 days"
          icon={<ShieldAlert className="h-4 w-4" />}
          iconBg="bg-indigo-500/15 border border-indigo-500/25"
          iconColor="text-indigo-400"
        />
      </div>

      {/* Discrepancy Alert Glass Banner */}
      {verificationAlerts.length > 0 && (
        <div className="flex items-center justify-between rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4.5 backdrop-blur-xl shadow-lg">
          <div className="flex items-center gap-3.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-[0_0_15px_rgba(244,63,94,0.4)] shrink-0">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white flex items-center gap-2">
                Contract Telemetry Discrepancy Detected
                <span className="font-mono text-[10px] text-rose-300 bg-rose-500/20 px-2 py-0.5 rounded-full border border-rose-500/30">
                  {verificationAlerts[0]?.service_name}
                </span>
              </h4>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Automated telemetry detected SLA violation on {verificationAlerts[0]?.customer?.name}. Proposed credit: {formatCurrency(verificationAlerts[0]?.proposed_credit)}.
              </p>
            </div>
          </div>
          <Link
            to="/admin/verification"
            className="flex items-center gap-1.5 rounded-full bg-rose-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-rose-500 transition-colors shadow-sm"
          >
            Review Discrepancy
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      )}

      {/* Recharts Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Monthly Revenue Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Monthly Recurring Revenue (MRR)</CardTitle>
              <CardDescription>Contracted vs collected telemetry revenue</CardDescription>
            </div>
            <span className="text-[11px] font-mono text-emerald-300 bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-0.5 rounded-full">
              +14.2% MoM
            </span>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics?.monthly_revenue || []}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={11} stroke="#64748b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                  stroke="#64748b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Revenue']}
                  contentStyle={{ backgroundColor: '#0c1220', color: '#fff', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.12)' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRev)" />
                <Area type="monotone" dataKey="target" stroke="#64748b" strokeDasharray="3 3" strokeWidth={1.5} fill="none" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Subscription Velocity Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Subscription Velocity</CardTitle>
              <CardDescription>New acquired accounts vs churned</CardDescription>
            </div>
            <span className="text-[11px] font-mono text-blue-300 bg-blue-500/15 border border-blue-500/25 px-2.5 py-0.5 rounded-full">
              Net Positive
            </span>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics?.subscription_growth || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={11} stroke="#64748b" />
                <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0c1220', color: '#fff', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.12)' }}
                />
                <Bar dataKey="new" name="New Subscriptions" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                <Bar dataKey="churned" name="Churned" fill="#f43f5e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Settlement Flow Line Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Settlement Flow</CardTitle>
              <CardDescription>Processed volume across automated gateways</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.payment_trends || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={11} stroke="#64748b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                  stroke="#64748b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Volume']}
                  contentStyle={{ backgroundColor: '#0c1220', color: '#fff', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.12)' }}
                />
                <Line type="monotone" dataKey="volume" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 3, fill: '#06b6d4' }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Invoice Status Distribution (Donut Chart) */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Invoice Health Distribution</CardTitle>
              <CardDescription>Status breakdown of billed amounts</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics?.invoice_distribution || []}
                  innerRadius={65}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {(metrics?.invoice_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: number) => [`${val}%`, 'Share']}
                  contentStyle={{ backgroundColor: '#0c1220', color: '#fff', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.12)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tables: Recent Subscriptions & Invoices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Recent Subscriptions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Recent Subscriptions</CardTitle>
              <CardDescription>Contracted accounts & operational state</CardDescription>
            </div>
            <Link
              to="/admin/subscriptions"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300"
            >
              View All →
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subscription</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Contract Price</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              {isSubsLoading ? (
                <TableLoadingState colSpan={4} />
              ) : subscriptions.length === 0 ? (
                <TableEmptyState title="No subscriptions" description="No subscriptions found." />
              ) : (
                <TableBody>
                  {subscriptions.slice(0, 4).map((sub) => {
                    const badge = getStatusBadgeVariant(sub.status);
                    return (
                      <TableRow key={sub.id}>
                        <TableCell className="font-mono text-xs font-semibold text-white">
                          <Link to="/admin/subscriptions" className="hover:text-blue-400">
                            {sub.subscription_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs text-slate-300">{sub.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs font-mono font-medium text-white">
                          {formatCurrency(sub.contracted_price, sub.currency)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={sub.status === 'active' ? 'success' : sub.status === 'paused' ? 'warning' : 'default'} size="sm">
                            {badge.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              )}
            </Table>
          </CardContent>
        </Card>

        {/* Attention Invoices */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Invoices Requiring Attention</CardTitle>
              <CardDescription>Overdue & pending settlement invoices</CardDescription>
            </div>
            <Link
              to="/admin/invoices"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300"
            >
              View All →
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Balance</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              {isInvoicesLoading ? (
                <TableLoadingState colSpan={5} />
              ) : invoices.length === 0 ? (
                <TableEmptyState title="No invoices" description="No invoices found." />
              ) : (
                <TableBody>
                  {invoices.slice(0, 4).map((inv) => {
                    const isOverdue = inv.status === 'overdue';
                    return (
                      <TableRow key={inv.id}>
                        <TableCell className="font-mono text-xs font-semibold text-white">
                          <Link to="/admin/invoices" className="hover:text-blue-400">
                            {inv.invoice_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs text-slate-300">{inv.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs text-slate-400 font-mono">
                          {formatDate(inv.due_date)}
                        </TableCell>
                        <TableCell className="text-xs font-mono font-bold text-white">
                          {formatCurrency(inv.balance_due, inv.currency)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={isOverdue ? 'danger' : inv.status === 'paid' ? 'success' : 'default'} size="sm">
                            {inv.status.toUpperCase()}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              )}
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
