import React, { useState } from 'react';
import { useNavigate, useLocation, NavLink } from 'react-router-dom';
import {
  Bell,
  Search,
  Building,
  User as UserIcon,
  LogOut,
  ChevronDown,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  Repeat,
  Receipt,
  ShieldCheck,
  Settings,
  LayoutDashboard,
} from 'lucide-react';
import { User, UserRole } from '../../types';
import { authService } from '../../services/auth';
import { cn } from '../../utils';

interface TopNavProps {
  user: User | null;
  onRoleChange: (role: UserRole) => void;
}

const NAV_PILLS = [
  { label: 'Overview', path: '/admin/overview', icon: LayoutDashboard },
  { label: 'Subscriptions', path: '/admin/subscriptions', icon: Repeat },
  { label: 'Billing & Invoices', path: '/admin/invoices', icon: Receipt },
  { label: 'Value Verification', path: '/admin/verification', icon: ShieldCheck, badge: '1 Alert' },
  { label: 'AI Copilot', path: '/admin/ai-insights', icon: Sparkles, badge: 'AI' },
  { label: 'Settings', path: '/admin/settings', icon: Settings },
];

export const TopNav: React.FC<TopNavProps> = ({ user, onRoleChange }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [orgOpen, setOrgOpen] = useState(false);

  const handleLogout = () => {
    authService.logout();
    navigate('/auth/login');
  };

  return (
    <div className="sticky top-0 z-40 w-full border-b border-black/[0.08] bg-white/80 backdrop-blur-xl">
      {/* Apple Store Minimal Navigation Header */}
      <header className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Left: Brand Identity with Paddle + Solana Monomark */}
        <div className="flex items-center gap-3">
          <NavLink to="/admin/overview" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-white font-bold text-xs shadow-xs transition-transform group-hover:scale-105">
              V
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-slate-900 text-sm tracking-tight">VERISUB</span>
              <span className="hidden sm:inline-block rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-mono text-slate-600">
                Fintech & Node
              </span>
            </div>
          </NavLink>

          {/* Solana PublicNode Live Telemetry Indicator Pill */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-[11px] font-mono">
            <span className="solana-pulse">
              <span></span>
              <span></span>
            </span>
            <span className="font-semibold text-slate-700">NODE LIVE</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500">32ms</span>
            <span className="text-slate-300">|</span>
            <span className="text-emerald-700 font-semibold">99.98% SLA</span>
          </div>
        </div>

        {/* Center: Apple Pill Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_PILLS.map((item) => {
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
                  'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-150 select-none',
                  isActive
                    ? 'bg-black/[0.08] text-[#1d1d1f] font-semibold'
                    : 'text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.04]'
                )}
              >
                <Icon className={cn('h-3.5 w-3.5', isActive ? 'text-[#0071e3]' : 'text-[#86868b]')} />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={cn(
                      'rounded-full px-1.5 py-0.2 text-[9px] font-mono font-bold leading-none',
                      item.badge === '1 Alert'
                        ? 'bg-rose-100 text-rose-700 border border-rose-200'
                        : 'bg-blue-100 text-[#0071e3] border border-blue-200'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Right: Quick Search, Role Switcher & Profile */}
        <div className="flex items-center gap-2.5">
          {/* Spotlight Search Pill */}
          <div className="hidden md:flex items-center gap-2 rounded-full bg-black/[0.04] border border-black/[0.06] px-3 py-1.5 text-xs text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.07] transition-all cursor-pointer">
            <Search className="h-3.5 w-3.5 text-[#86868b]" />
            <span className="text-[11px]">Quick Search</span>
            <kbd className="rounded bg-black/[0.06] px-1.5 py-0.2 font-mono text-[9px] text-[#6e6e73]">⌘K</kbd>
          </div>

          {/* Apple Segmented Control Role Switcher */}
          <div className="flex items-center rounded-full bg-[#e8e8ed] p-0.5 border border-black/[0.05] text-xs font-medium">
            <button
              onClick={() => {
                onRoleChange('admin');
                navigate('/admin/overview');
              }}
              className={cn(
                'rounded-full px-2.5 py-1 text-[11px] transition-all duration-150',
                user?.role === 'admin'
                  ? 'bg-white text-[#1d1d1f] font-semibold shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              )}
            >
              Admin
            </button>
            <button
              onClick={() => {
                onRoleChange('staff');
                navigate('/admin/overview');
              }}
              className={cn(
                'rounded-full px-2.5 py-1 text-[11px] transition-all duration-150',
                user?.role === 'staff'
                  ? 'bg-white text-[#1d1d1f] font-semibold shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              )}
            >
              Staff
            </button>
            <button
              onClick={() => {
                onRoleChange('customer');
                navigate('/portal/dashboard');
              }}
              className={cn(
                'rounded-full px-2.5 py-1 text-[11px] transition-all duration-150',
                user?.role === 'customer'
                  ? 'bg-white text-[#1d1d1f] font-semibold shadow-xs'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f]'
              )}
            >
              Portal
            </button>
          </div>

          {/* Organization Pill */}
          <div className="relative hidden xl:block">
            <button
              onClick={() => setOrgOpen(!orgOpen)}
              className="flex items-center gap-1.5 rounded-full border border-black/[0.08] bg-white px-3 py-1 text-xs text-[#1d1d1f] hover:bg-[#f5f5f7] transition-colors shadow-2xs"
            >
              <Building className="h-3 w-3 text-[#0071e3]" />
              <span className="max-w-[100px] truncate">{user?.organization_name || 'Acme Inc'}</span>
              <ChevronDown className="h-3 w-3 text-[#86868b]" />
            </button>

            {orgOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-black/[0.08] bg-white p-2 shadow-2xl z-50">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-[#86868b] uppercase tracking-wider">
                  Organization
                </div>
                <button
                  onClick={() => setOrgOpen(false)}
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium text-[#1d1d1f] hover:bg-black/[0.04]"
                >
                  <span>{user?.organization_name || 'Verisub Enterprise'}</span>
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0071e3]" />
                </button>
              </div>
            )}
          </div>

          {/* Notifications Icon Pill */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative rounded-full p-2 text-[#6e6e73] hover:bg-black/[0.05] hover:text-[#1d1d1f] transition-colors"
              title="Notifications"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#0071e3]" />
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-black/[0.08] bg-white p-3.5 shadow-2xl z-50">
                <div className="flex items-center justify-between border-b border-black/[0.06] pb-2.5">
                  <span className="text-xs font-semibold text-[#1d1d1f]">
                    Live Telemetry Alerts
                  </span>
                  <span className="rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-mono font-bold text-[#0071e3]">
                    2 New
                  </span>
                </div>
                <div className="mt-3 space-y-2">
                  <div className="rounded-xl bg-rose-50 border border-rose-200 p-2.5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-rose-800">
                      <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
                      SLA Discrepancy Detected
                    </div>
                    <p className="mt-1 text-[11px] text-[#6e6e73]">
                      SUB-2026-0412 recorded 168 min downtime. $249.90 credit proposed.
                    </p>
                  </div>
                  <div className="rounded-xl bg-blue-50 border border-blue-200 p-2.5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-[#0071e3]">
                      <Sparkles className="h-3.5 w-3.5 text-[#0071e3]" />
                      AI Telemetry Analysis
                    </div>
                    <p className="mt-1 text-[11px] text-[#6e6e73]">
                      Quotation QUO-2026-0098 contains manual discount of $600.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Pill */}
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-1.5 rounded-full p-1 hover:bg-black/[0.05] transition-colors"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1d1d1f] text-xs font-bold text-white uppercase shadow-2xs">
                {user?.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-black/[0.08] bg-white p-2 shadow-2xl z-50">
                <div className="border-b border-black/[0.06] px-3 py-2">
                  <p className="text-xs font-semibold text-[#1d1d1f]">{user?.full_name}</p>
                  <p className="text-[11px] text-[#6e6e73] font-mono truncate">{user?.email}</p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      setProfileOpen(false);
                      navigate('/admin/settings');
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs text-[#1d1d1f] hover:bg-black/[0.04]"
                  >
                    <UserIcon className="h-3.5 w-3.5 text-[#86868b]" />
                    Account Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
    </div>
  );
};
