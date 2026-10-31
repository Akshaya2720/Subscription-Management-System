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
    badge: 'Smart',
    badgeVariant: 'purple',
  },
  {
    label: 'Settings & Security',
    path: '/admin/settings',
    icon: Settings,
    roles: ['admin', 'staff'],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ role = 'admin' }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const filteredNav = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-black/[0.08] bg-white transition-all duration-300 z-30 select-none text-[#1d1d1f]',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-5 border-b border-black/[0.06]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#1d1d1f] text-white font-bold tracking-wider text-sm shadow-2xs">
            V
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-[#1d1d1f] tracking-tight text-sm leading-none flex items-center gap-1.5">
                VERISUB
                <span className="rounded-full bg-black/[0.05] border border-black/[0.08] px-1.5 py-0.2 text-[9px] font-mono font-medium text-[#6e6e73]">
                  Store
                </span>
              </span>
              <span className="text-[10px] text-[#6e6e73] tracking-wider mt-1 uppercase">
                {role === 'staff' ? 'Staff Workspace' : 'SaaS Console'}
              </span>
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-full p-1.5 text-[#6e6e73] hover:bg-black/[0.05] hover:text-[#1d1d1f] transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Main Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {!collapsed && (
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-[#86868b]">
            Platform
          </p>
        )}

        {filteredNav.map((item) => {
          const Icon = item.icon;
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
                'group flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all duration-150',
                isActive
                  ? 'bg-black/[0.06] text-[#1d1d1f] font-semibold'
                  : 'text-[#6e6e73] hover:bg-black/[0.03] hover:text-[#1d1d1f]'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  'h-4 w-4 shrink-0 transition-colors',
                  isActive ? 'text-[#0071e3]' : 'text-[#86868b] group-hover:text-[#1d1d1f]'
                )}
              />
              {!collapsed && <span className="flex-1">{item.label}</span>}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    'rounded-full px-1.5 py-0.5 text-[10px] font-mono font-medium',
                    item.badgeVariant === 'danger'
                      ? 'bg-rose-100 text-rose-700'
                      : 'bg-blue-50 text-[#0071e3]'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>
    </aside>
  );
};
