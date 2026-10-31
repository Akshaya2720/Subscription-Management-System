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
  Receipt,
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
  const [statusFilter] = useState('all');

  // Fetch live metrics
  const { data: metrics } = useQuery({
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

  const verificationAlerts = verifications.filter((v) => v.discrepancy_detected);

  return (
    <div className="space-y-6 text-left">
      {/* Apple Shelf Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar select-none">
        <button
          onClick={() => navigate('/admin/subscriptions')}
          className="flex items-center gap-2 rounded-full bg-[#0071e3] px-4 py-1.5 text-xs font-semibold text-white shadow-xs transition-all hover:bg-[#0077ed]"
        >
          <Repeat className="h-3.5 w-3.5" />
          <span>Active Subscriptions ({metrics?.active_subscriptions || 2})</span>
        </button>

        <button
          onClick={() => navigate('/admin/verification')}
          className="flex items-center gap-2 rounded-full bg-white border border-black/[0.08] px-4 py-1.5 text-xs font-medium text-[#1d1d1f] hover:bg-[#f5f5f7] shadow-2xs transition-all"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span>Hash-Chain Verified</span>
        </button>

        <button
          onClick={() => navigate('/admin/invoices')}
          className="flex items-center gap-2 rounded-full bg-white border border-black/[0.08] px-4 py-1.5 text-xs font-medium text-[#1d1d1f] hover:bg-[#f5f5f7] shadow-2xs transition-all"
        >
          <Receipt className="h-3.5 w-3.5 text-[#0071e3]" />
          <span>Automated Billing Ledger</span>
        </button>

        {verificationAlerts.length > 0 && (
          <button
            onClick={() => navigate('/admin/verification')}
            className="flex items-center gap-2 rounded-full bg-rose-50 border border-rose-200 px-4 py-1.5 text-xs font-semibold text-rose-700 shadow-2xs hover:bg-rose-100 transition-all"
          >
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
            <span>1 SLA Telemetry Discrepancy</span>
          </button>
        )}
      </div>

      {/* Hero Header & Quick Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1d1d1f] font-sans">
              Platform Overview
            </h1>
            <span className="rounded-full bg-black/[0.05] border border-black/[0.06] px-2.5 py-0.5 text-[10px] font-mono font-medium text-[#6e6e73]">
              Store Edition
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#6e6e73] mt-1">
            Contract-to-bill verification telemetry, recurring revenue velocity, and automated settlements
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs shadow-xs">
            <Filter className="h-3.5 w-3.5 text-slate-500" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-transparent font-medium text-slate-900 outline-none cursor-pointer"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="1y">This Year</option>
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
            leftIcon={<ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />}
          >
            SLA Verification
          </Button>
        </div>
      </div>

      {/* Solana PublicNode Real-Time Node Health & Telemetry Bar */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white font-mono font-bold text-sm shadow-xs shrink-0">
              ⚡
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="solana-pulse">
                  <span></span>
                  <span></span>
                </span>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Solana PublicNode RPC & Telemetry Engine
                </h3>
                <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-700">
                  100% OPERATIONAL
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                Real-time node telemetry stream • Deterministic SLA verification active • SHA-256 ledger linked
              </p>
            </div>
          </div>

          {/* Real-time Telemetry Metrics Chips */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 border border-slate-200 px-3 py-1.5">
              <span className="text-slate-500 text-[11px]">RPC Latency:</span>
              <span className="text-emerald-700 font-bold">28ms</span>
              <span className="rounded-full bg-emerald-100 text-emerald-800 text-[9px] px-1.5 font-bold">P95</span>
            </div>

            <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 border border-slate-200 px-3 py-1.5">
              <span className="text-slate-500 text-[11px]">SLA Delivery:</span>
              <span className="text-emerald-700 font-bold">99.98%</span>
            </div>

            <div className="flex items-center gap-1.5 rounded-lg bg-slate-50 border border-slate-200 px-3 py-1.5">
              <span className="text-slate-500 text-[11px]">Ledger Block:</span>
              <span className="text-slate-800 font-bold">#284,912</span>
            </div>

            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate('/admin/audit')}
              leftIcon={<ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />}
            >
              Verify SHA-256 Chain
            </Button>
          </div>
        </div>
      </div>

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
        <StatCard
          title="Active Subs"
          value={metrics?.active_subscriptions || 0}
          change={metrics?.active_subscriptions_change}
          icon={<Repeat className="h-4 w-4" />}
          iconBg="bg-blue-50 border border-blue-100"
          iconColor="text-[#0071e3]"
        />

        <StatCard
          title="Revenue Recv"
          value={formatCurrency(metrics?.revenue_received)}
          change={metrics?.revenue_change}
          icon={<DollarSign className="h-4 w-4" />}
          iconBg="bg-emerald-50 border border-emerald-100"
          iconColor="text-[#0a6634]"
        />

        <StatCard
          title="Outstanding"
          value={formatCurrency(metrics?.outstanding_amount)}
          change={metrics?.outstanding_change}
          icon={<Clock className="h-4 w-4" />}
          iconBg="bg-amber-50 border border-amber-100"
          iconColor="text-[#9a5b00]"
        />

        <StatCard
          title="Overdue"
          value={metrics?.overdue_invoices || 0}
          badge={metrics?.overdue_invoices ? 'Action Required' : '0 Alerts'}
          icon={<AlertCircle className="h-4 w-4" />}
          iconBg="bg-rose-50 border border-rose-100"
          iconColor="text-[#c41c26]"
        />

        <StatCard
          title="Accounts"
          value={metrics?.total_customers || 0}
          change={metrics?.total_customers_change}
          icon={<Users className="h-4 w-4" />}
          iconBg="bg-indigo-50 border border-indigo-100"
          iconColor="text-[#5856d6]"
        />

        <StatCard
          title="Renewals"
          value={metrics?.upcoming_renewals || 0}
          subtitle="Next 30 days"
          icon={<ShieldAlert className="h-4 w-4" />}
          iconBg="bg-purple-50 border border-purple-100"
          iconColor="text-[#af52de]"
        />
      </div>

      {/* Discrepancy Alert Banner */}
      {verificationAlerts.length > 0 && (
        <div className="flex items-center justify-between rounded-2xl border border-rose-200 bg-rose-50 p-4.5 shadow-2xs">
          <div className="flex items-center gap-3.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-2xs shrink-0">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#1d1d1f] flex items-center gap-2">
                Contract Telemetry Discrepancy Detected
                <span className="font-mono text-[10px] text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full border border-rose-200">
                  {verificationAlerts[0]?.service_name}
                </span>
              </h4>
              <p className="text-[11px] text-[#6e6e73] mt-0.5">
                Automated telemetry detected SLA violation on {verificationAlerts[0]?.customer?.name}. Proposed credit: {formatCurrency(verificationAlerts[0]?.proposed_credit)}.
              </p>
            </div>
          </div>
          <Link
            to="/admin/verification"
            className="flex items-center gap-1.5 rounded-full bg-rose-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 transition-colors shadow-2xs"
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
            <span className="text-[11px] font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full font-semibold">
              +14.2% MoM
            </span>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics?.monthly_revenue || []}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0071e3" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#0071e3" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5ea" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={11} stroke="#86868b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                  stroke="#86868b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Revenue']}
                  contentStyle={{ backgroundColor: '#ffffff', color: '#1d1d1f', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#0071e3" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRev)" />
                <Area type="monotone" dataKey="target" stroke="#86868b" strokeDasharray="3 3" strokeWidth={1.5} fill="none" />
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
            <span className="text-[11px] font-mono text-[#0071e3] bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full font-semibold">
              Net Positive
            </span>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics?.subscription_growth || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5ea" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={11} stroke="#86868b" />
                <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="#86868b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', color: '#1d1d1f', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                />
                <Bar dataKey="new" name="New Subscriptions" fill="#0071e3" radius={[6, 6, 0, 0]} />
                <Bar dataKey="churned" name="Churned" fill="#e8e8ed" radius={[6, 6, 0, 0]} />
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
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5ea" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={11} stroke="#86868b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                  stroke="#86868b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Volume']}
                  contentStyle={{ backgroundColor: '#ffffff', color: '#1d1d1f', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
                />
                <Line type="monotone" dataKey="volume" stroke="#0071e3" strokeWidth={2.5} dot={{ r: 3, fill: '#0071e3' }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Invoice Status Distribution */}
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
                  contentStyle={{ backgroundColor: '#ffffff', color: '#1d1d1f', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
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
              className="text-xs font-semibold text-[#0071e3] hover:underline"
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
                        <TableCell className="font-mono text-xs font-semibold text-[#0071e3]">
                          <Link to="/admin/subscriptions" className="hover:underline">
                            {sub.subscription_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs text-[#1d1d1f] font-medium">{sub.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs font-mono font-medium text-[#1d1d1f]">
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
              className="text-xs font-semibold text-[#0071e3] hover:underline"
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
                        <TableCell className="font-mono text-xs font-semibold text-[#0071e3]">
                          <Link to="/admin/invoices" className="hover:underline">
                            {inv.invoice_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs text-[#1d1d1f] font-medium">{inv.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs text-[#6e6e73] font-mono">
                          {formatDate(inv.due_date)}
                        </TableCell>
                        <TableCell className="text-xs font-mono font-bold text-[#1d1d1f]">
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
