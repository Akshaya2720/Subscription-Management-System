import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Package,
  Layers,
  FileCheck2,
  Repeat,
  Zap,
  Receipt,
  CreditCard,
  Percent,
  ShieldCheck,
  BrainCircuit,
  History,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
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
  badgeColor?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', path: '/admin/overview', icon: LayoutDashboard, roles: ['admin', 'staff'] },
  { label: 'Customers', path: '/admin/customers', icon: Users, roles: ['admin', 'staff'] },
  { label: 'Products', path: '/admin/products', icon: Package, roles: ['admin'] },
  { label: 'Plans', path: '/admin/plans', icon: Layers, roles: ['admin'] },
  { label: 'Quotations', path: '/admin/quotations', icon: FileCheck2, roles: ['admin', 'staff'] },
  { label: 'Subscriptions', path: '/admin/subscriptions', icon: Repeat, roles: ['admin', 'staff'] },
  { label: 'Billing', path: '/admin/billing', icon: Zap, roles: ['admin'] },
  { label: 'Invoices', path: '/admin/invoices', icon: Receipt, roles: ['admin', 'staff'] },
  { label: 'Payments', path: '/admin/payments', icon: CreditCard, roles: ['admin', 'staff'] },
  { label: 'Discounts', path: '/admin/discounts', icon: Percent, roles: ['admin'] },
  {
    label: 'Value Verification',
    path: '/admin/verification',
    icon: ShieldCheck,
    roles: ['admin', 'staff'],
    badge: '1 Alert',
    badgeColor: 'bg-rose-500 text-white',
  },
  {
    label: 'AI Insights',
    path: '/admin/ai-insights',
    icon: BrainCircuit,
    roles: ['admin', 'staff'],
    badge: 'New',
    badgeColor: 'bg-brand-500 text-white',
  },
  { label: 'Audit Trail', path: '/admin/audit', icon: History, roles: ['admin'] },
  { label: 'Reports', path: '/admin/reports', icon: BarChart3, roles: ['admin'] },
  { label: 'Settings', path: '/admin/settings', icon: Settings, roles: ['admin'] },
];

export const Sidebar: React.FC<SidebarProps> = ({ role = 'admin' }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const filteredNav = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-slate-200 bg-white transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 z-30 select-none',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm font-black tracking-wider text-base">
            V
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-extrabold text-slate-900 tracking-tight text-base leading-none dark:text-white">
                VERISUB
              </span>
              <span className="text-[10px] uppercase font-semibold text-brand-600 dark:text-brand-400 tracking-widest mt-0.5">
                {role === 'staff' ? 'Staff Portal' : 'Enterprise Admin'}
              </span>
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {filteredNav.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold transition-colors',
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-100'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  'h-4 w-4 shrink-0 transition-colors',
                  isActive
                    ? 'text-brand-600 dark:text-brand-400'
                    : 'text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300'
                )}
              />

              {!collapsed && (
                <span className="flex-1 truncate tracking-wide">{item.label}</span>
              )}

              {!collapsed && item.badge && (
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-bold leading-none',
                    item.badgeColor || 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* System Integrity Footer Status */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5 rounded-xl bg-slate-50 p-2.5 text-xs text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
            <ShieldAlert className="h-4 w-4 text-emerald-500 shrink-0" />
            <div className="truncate">
              <p className="font-semibold text-[11px] text-slate-900 dark:text-slate-100">
                Hash-Chain Verified
              </p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                Contract integrity active
              </p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
