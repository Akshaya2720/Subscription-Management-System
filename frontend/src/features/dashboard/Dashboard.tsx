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
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableLoading, TableEmpty } from '../../components/common/Table';
import { dashboardService } from '../../services/dashboardService';
import { subscriptionService } from '../../services/subscriptionService';
import { invoiceService } from '../../services/invoiceService';
import { verificationService } from '../../services/verificationService';
import { formatCurrency, formatDate, getStatusBadgeVariant } from '../../utils';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
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
    <div className="space-y-8">
      {/* Page Title & Global Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Executive Subscription Dashboard
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time subscription metrics, contract billing verification telemetry & revenue health
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs dark:border-slate-800 dark:bg-slate-900 shadow-2xs">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-transparent font-medium text-slate-700 outline-none dark:text-slate-200 cursor-pointer"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="1y">This Year</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs dark:border-slate-800 dark:bg-slate-900 shadow-2xs">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent font-medium text-slate-700 outline-none dark:text-slate-200 cursor-pointer"
            >
              <option value="all">All Subscriptions</option>
              <option value="active">Active Only</option>
              <option value="paused">Paused Only</option>
              <option value="closed">Closed Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Active Subs"
          value={metrics?.active_subscriptions || 0}
          change={metrics?.active_subscriptions_change}
          icon={<Repeat className="h-5 w-5" />}
          iconBg="bg-blue-50 dark:bg-blue-950/60"
          iconColor="text-blue-600 dark:text-blue-400"
        />

        <StatCard
          title="Revenue Received"
          value={formatCurrency(metrics?.revenue_received)}
          change={metrics?.revenue_change}
          icon={<DollarSign className="h-5 w-5" />}
          iconBg="bg-emerald-50 dark:bg-emerald-950/60"
          iconColor="text-emerald-600 dark:text-emerald-400"
        />

        <StatCard
          title="Outstanding"
          value={formatCurrency(metrics?.outstanding_amount)}
          change={metrics?.outstanding_change}
          icon={<Clock className="h-5 w-5" />}
          iconBg="bg-amber-50 dark:bg-amber-950/60"
          iconColor="text-amber-600 dark:text-amber-400"
        />

        <StatCard
          title="Overdue Invoices"
          value={metrics?.overdue_invoices || 0}
          badge={metrics?.overdue_invoices ? 'Action Required' : 'Clean'}
          icon={<AlertCircle className="h-5 w-5" />}
          iconBg="bg-rose-50 dark:bg-rose-950/60"
          iconColor="text-rose-600 dark:text-rose-400"
        />

        <StatCard
          title="Total Customers"
          value={metrics?.total_customers || 0}
          change={metrics?.total_customers_change}
          icon={<Users className="h-5 w-5" />}
          iconBg="bg-purple-50 dark:bg-purple-950/60"
          iconColor="text-purple-600 dark:text-purple-400"
        />

        <StatCard
          title="Upcoming Renewals"
          value={metrics?.upcoming_renewals || 0}
          subtitle="Next 30 days"
          icon={<ShieldAlert className="h-5 w-5" />}
          iconBg="bg-indigo-50 dark:bg-indigo-950/60"
          iconColor="text-indigo-600 dark:text-indigo-400"
        />
      </div>

      {/* Verification Discrepancy Banner if any */}
      {verificationAlerts.length > 0 && (
        <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50/80 p-4 dark:border-rose-900 dark:bg-rose-950/30">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-600 text-white">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-rose-900 dark:text-rose-200">
                Contract-to-Bill Discrepancy Flagged
              </h4>
              <p className="text-xs text-rose-700 dark:text-rose-400">
                Automated telemetry detected SLA violation on {verificationAlerts[0]?.customer?.name}. Proposed bill credit: {formatCurrency(verificationAlerts[0]?.proposed_credit)}.
              </p>
            </div>
          </div>
          <Link
            to="/admin/verification"
            className="flex items-center gap-1 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 shadow-sm transition-colors"
          >
            Review Discrepancy
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      )}

      {/* Recharts Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Revenue Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Recurring Revenue (MRR)</CardTitle>
            <CardDescription>Target vs actual collected revenue over past cycles</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics?.monthly_revenue || []}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  stroke="#64748b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Revenue']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', border: 'none' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#4f46e5" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRev)" />
                <Area type="monotone" dataKey="target" stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1.5} fill="none" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Subscription Growth Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Subscription Velocity</CardTitle>
            <CardDescription>New subscriptions acquired vs churned</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics?.subscription_growth || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', border: 'none' }}
                />
                <Bar dataKey="new" name="New Subscriptions" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="churned" name="Churned" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Payment Trends Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Payment Flow</CardTitle>
            <CardDescription>Processed volume across all payment gateways</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.payment_trends || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  stroke="#64748b"
                  tickFormatter={(v) => `$${v / 1000}k`}
                />
                <Tooltip
                  formatter={(val: number) => [formatCurrency(val), 'Volume']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', border: 'none' }}
                />
                <Line type="monotone" dataKey="volume" stroke="#0ea5e9" strokeWidth={2.5} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Invoice Status Distribution (Donut Chart) */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Health Distribution</CardTitle>
            <CardDescription>Current status breakdown of total generated invoices</CardDescription>
          </CardHeader>
          <CardContent className="h-72 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics?.invoice_distribution || []}
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {(metrics?.invoice_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: number) => [`${val}%`, 'Share']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', border: 'none' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Subscriptions & Recent Invoices Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Subscriptions Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Subscriptions</CardTitle>
              <CardDescription>Latest contracted accounts and billing status</CardDescription>
            </div>
            <Link
              to="/admin/subscriptions"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              View All
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subscription</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              {isSubsLoading ? (
                <TableLoading columnsCount={4} rowsCount={3} />
              ) : subscriptions.length === 0 ? (
                <TableEmpty title="No subscriptions" description="No subscriptions found." colSpan={4} />
              ) : (
                <TableBody>
                  {subscriptions.slice(0, 4).map((sub) => {
                    const badge = getStatusBadgeVariant(sub.status);
                    return (
                      <TableRow key={sub.id}>
                        <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                          <Link to={`/admin/subscriptions`} className="hover:text-brand-600">
                            {sub.subscription_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs">{sub.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs font-medium">
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

        {/* Recent / Overdue Invoices Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Invoices Requiring Attention</CardTitle>
              <CardDescription>Overdue and upcoming due invoices</CardDescription>
            </div>
            <Link
              to="/admin/invoices"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              View All
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
                <TableLoading columnsCount={5} rowsCount={3} />
              ) : invoices.length === 0 ? (
                <TableEmpty title="No invoices" description="No invoices found." colSpan={5} />
              ) : (
                <TableBody>
                  {invoices.slice(0, 4).map((inv) => {
                    const isOverdue = inv.status === 'overdue';
                    return (
                      <TableRow key={inv.id}>
                        <TableCell className="font-semibold text-xs text-slate-900 dark:text-white">
                          <Link to="/admin/invoices" className="hover:text-brand-600">
                            {inv.invoice_number}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs">{inv.customer?.name || 'Customer'}</TableCell>
                        <TableCell className="text-xs text-slate-500">
                          {formatDate(inv.due_date)}
                        </TableCell>
                        <TableCell className="text-xs font-bold text-slate-900 dark:text-white">
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
