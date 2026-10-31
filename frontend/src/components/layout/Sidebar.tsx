import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Repeat,
  Receipt,
  ShieldCheck,
  Sparkles,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Layers,
} from 'lucide-react';
import { cn } from '../../utils';
import { UserRole } from '../../types';

interface SidebarProps {
  role?: UserRole;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: UserRole[];
  badge?: string;
  badgeVariant?: 'purple' | 'danger' | 'success';
}

// Simplified high-level navigation (Cerebrium minimal style)
const NAV_ITEMS: NavItem[] = [
  {
    label: 'Overview',
    path: '/admin/overview',
    icon: LayoutDashboard,
    roles: ['admin', 'staff'],
  },
  {
    label: 'Subscriptions',
    path: '/admin/subscriptions',
    icon: Repeat,
    roles: ['admin', 'staff'],
    badge: '3 Active',
    badgeVariant: 'purple',
  },
  {
    label: 'Billing & Invoices',
    path: '/admin/invoices',
    icon: Receipt,
    roles: ['admin', 'staff'],
  },
  {
    label: 'Value Verification',
    path: '/admin/verification',
    icon: ShieldCheck,
    roles: ['admin', 'staff'],
    badge: '1 Alert',
    badgeVariant: 'danger',
  },
  {
    label: 'AI Copilot',
    path: '/admin/ai-insights',
    icon: Sparkles,
    roles: ['admin', 'staff'],
    badge: 'AI',
    badgeVariant: 'purple',
  },
  {
    label: 'Settings & Audit',
    path: '/admin/settings',
    icon: Settings,
    roles: ['admin'],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ role = 'admin' }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const filteredNav = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-white/[0.08] bg-[#0a0c10] transition-all duration-300 z-30 select-none',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-5 border-b border-white/[0.08]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-glow-sm font-bold tracking-wider text-sm border border-violet-400/30">
            V
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-white tracking-tight text-sm leading-none flex items-center gap-1.5">
                VERISUB
                <span className="rounded-full bg-violet-500/10 border border-violet-500/30 px-1.5 py-0.2 text-[9px] font-mono font-medium text-violet-400">
                  v2.4
                </span>
              </span>
              <span className="text-[10px] text-slate-400 tracking-wider mt-1 uppercase">
                {role === 'staff' ? 'Staff Workspace' : 'SaaS Console'}
              </span>
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-lg p-1 text-slate-400 hover:bg-white/[0.06] hover:text-white transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Main Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {!collapsed && (
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Platform
          </p>
        )}

        {filteredNav.map((item) => {
          const Icon = item.icon;
          // Match active route: either exact or sub-route
          const isActive =
            location.pathname === item.path ||
            (item.path === '/admin/subscriptions' &&
              ['/admin/subscriptions', '/admin/quotations', '/admin/plans', '/admin/products', '/admin/customers'].some(
                (p) => location.pathname.startsWith(p)
              )) ||
            (item.path === '/admin/invoices' &&
              ['/admin/invoices', '/admin/billing', '/admin/payments', '/admin/discounts'].some((p) =>
                location.pathname.startsWith(p)
              )) ||
            (item.path === '/admin/settings' &&
              ['/admin/settings', '/admin/audit', '/admin/reports'].some((p) =>
                location.pathname.startsWith(p)
              )) ||
            (item.path !== '/admin/overview' && location.pathname.startsWith(item.path));

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all duration-150',
                isActive
                  ? 'bg-violet-600/15 text-white border border-violet-500/30 shadow-[0_0_12px_rgba(139,92,246,0.15)]'
                  : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200 border border-transparent'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  'h-4 w-4 shrink-0 transition-colors',
                  isActive ? 'text-violet-400' : 'text-slate-500 group-hover:text-slate-300'
                )}
              />

              {!collapsed && (
                <span className="flex-1 truncate tracking-wide">{item.label}</span>
              )}

              {!collapsed && item.badge && (
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-[9px] font-mono font-semibold uppercase leading-none border',
                    item.badgeVariant === 'danger' &&
                      'bg-rose-500/15 text-rose-400 border-rose-500/30',
                    item.badgeVariant === 'purple' &&
                      'bg-violet-500/15 text-violet-300 border-violet-500/30',
                    (!item.badgeVariant || item.badgeVariant === 'success') &&
                      'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Contract Verification Health Indicator */}
      {!collapsed && (
        <div className="p-3 border-t border-white/[0.08]">
          <div className="flex items-center gap-2.5 rounded-lg bg-[#0e1117] p-2.5 text-xs border border-white/[0.06]">
            <div className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            <div className="truncate">
              <p className="font-semibold text-[11px] text-white flex items-center gap-1">
                Telemetry Connected
              </p>
              <p className="text-[10px] text-slate-400 font-mono truncate">
                Hash-Chain: #8f04c...9d
              </p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
