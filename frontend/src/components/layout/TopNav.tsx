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
    <div className="sticky top-3 z-40 w-full px-4 sm:px-6 mb-4">
      {/* Supaste Floating Dynamic Island Navigation */}
      <header className="mx-auto flex h-14 max-w-7xl items-center justify-between rounded-full border border-white/[0.13] bg-[#0c1220]/85 px-4 sm:px-5 backdrop-blur-2xl shadow-island">
        {/* Left: Brand Identity with Sapphire Icon */}
        <div className="flex items-center gap-3">
          <NavLink to="/admin/overview" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-cyan-500 text-white font-black text-xs shadow-glow-blue border border-white/20 transition-transform group-hover:scale-105">
              V
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white text-sm tracking-tight">VERISUB</span>
              <span className="hidden sm:inline-block rounded-full bg-blue-500/15 border border-blue-500/30 px-2 py-0.2 text-[9px] font-mono text-blue-300">
                macOS
              </span>
            </div>
          </NavLink>
        </div>

        {/* Center: Floating Navigation Pills */}
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
                  'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 select-none',
                  isActive
                    ? 'bg-white/[0.12] text-white border border-white/[0.18] shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-white/[0.05] border border-transparent'
                )}
              >
                <Icon className={cn('h-3.5 w-3.5', isActive ? 'text-blue-400' : 'text-slate-400')} />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={cn(
                      'rounded-full px-1.5 py-0.2 text-[9px] font-mono font-bold leading-none',
                      item.badge === '1 Alert'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
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
          {/* Spotlight Search Shortcut Pill */}
          <div className="hidden md:flex items-center gap-2 rounded-full bg-white/[0.05] border border-white/[0.1] px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:border-white/[0.18] transition-all cursor-pointer">
            <Search className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-[11px]">Quick Search</span>
            <kbd className="rounded bg-white/[0.1] px-1.5 py-0.2 font-mono text-[9px] text-slate-300">⌘K</kbd>
          </div>

          {/* Dynamic Role Switcher Pill (Admin / Staff / Customer) */}
          <div className="flex items-center rounded-full bg-white/[0.06] p-0.5 border border-white/[0.1] text-xs font-medium">
            <button
              onClick={() => {
                onRoleChange('admin');
                navigate('/admin/overview');
              }}
              className={cn(
                'rounded-full px-2.5 py-1 text-[11px] transition-all duration-150',
                user?.role === 'admin'
                  ? 'bg-blue-600 text-white font-semibold shadow-glow-blue'
                  : 'text-slate-400 hover:text-slate-200'
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
                  ? 'bg-blue-600 text-white font-semibold shadow-glow-blue'
                  : 'text-slate-400 hover:text-slate-200'
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
                  ? 'bg-blue-600 text-white font-semibold shadow-glow-blue'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              Portal
            </button>
          </div>

          {/* Organization Pill */}
          <div className="relative hidden xl:block">
            <button
              onClick={() => setOrgOpen(!orgOpen)}
              className="flex items-center gap-1.5 rounded-full border border-white/[0.1] bg-white/[0.05] px-3 py-1 text-xs text-slate-300 hover:bg-white/[0.09] transition-colors"
            >
              <Building className="h-3 w-3 text-blue-400" />
              <span className="max-w-[100px] truncate">{user?.organization_name || 'Acme Inc'}</span>
              <ChevronDown className="h-3 w-3 text-slate-400" />
            </button>

            {orgOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-white/[0.14] bg-[#0c1220]/95 p-2 shadow-2xl backdrop-blur-3xl z-50">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Organization
                </div>
                <button
                  onClick={() => setOrgOpen(false)}
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium text-white hover:bg-white/[0.08]"
                >
                  <span>{user?.organization_name || 'Verisub Enterprise'}</span>
                  <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
                </button>
              </div>
            )}
          </div>

          {/* Notifications Icon Pill */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative rounded-full p-2 text-slate-400 hover:bg-white/[0.08] hover:text-white transition-colors"
              title="Notifications"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.9)]" />
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-white/[0.14] bg-[#0c1220]/95 p-3.5 shadow-2xl backdrop-blur-3xl z-50">
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
                  <span className="text-xs font-semibold text-white">
                    Live Telemetry Alerts
                  </span>
                  <span className="rounded-full bg-blue-500/20 border border-blue-500/30 px-2 py-0.5 text-[10px] font-mono font-bold text-blue-300">
                    2 New
                  </span>
                </div>
                <div className="mt-3 space-y-2">
                  <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-2.5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-rose-300">
                      <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
                      SLA Discrepancy Detected
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400">
                      SUB-2026-0412 recorded 168 min downtime. $249.90 credit proposed.
                    </p>
                  </div>
                  <div className="rounded-xl bg-blue-500/10 border border-blue-500/20 p-2.5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-blue-300">
                      <Sparkles className="h-3.5 w-3.5 text-blue-400" />
                      AI Telemetry Analysis
                    </div>
                    <p className="mt-1 text-[11px] text-slate-400">
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
              className="flex items-center gap-1.5 rounded-full p-1 hover:bg-white/[0.08] transition-colors"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 text-xs font-bold text-white uppercase shadow-sm border border-white/20">
                {user?.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-white/[0.14] bg-[#0c1220]/95 p-2 shadow-2xl backdrop-blur-3xl z-50">
                <div className="border-b border-white/[0.08] px-3 py-2">
                  <p className="text-xs font-semibold text-white">{user?.full_name}</p>
                  <p className="text-[11px] text-slate-400 font-mono truncate">{user?.email}</p>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      setProfileOpen(false);
                      navigate('/admin/settings');
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-300 hover:bg-white/[0.08] hover:text-white"
                  >
                    <UserIcon className="h-3.5 w-3.5 text-slate-400" />
                    Account Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/10"
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
