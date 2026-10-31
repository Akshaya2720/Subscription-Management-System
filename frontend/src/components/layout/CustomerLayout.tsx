import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Repeat,
  Receipt,
  CreditCard,
  Activity,
  AlertTriangle,
  HelpCircle,
  User as UserIcon,
  LogOut,
  Building,
  ArrowLeftRight,
} from 'lucide-react';
import { cn } from '../../utils';
import { authService } from '../../services/auth';

const CUSTOMER_NAV = [
  { label: 'Overview', path: '/portal/dashboard', icon: LayoutDashboard },
  { label: 'My Subscriptions', path: '/portal/subscriptions', icon: Repeat },
  { label: 'Invoices & Billing', path: '/portal/invoices', icon: Receipt },
  { label: 'Payment History', path: '/portal/payments', icon: CreditCard },
  { label: 'Service Telemetry', path: '/portal/services', icon: Activity },
  { label: 'Disputes & SLA', path: '/portal/disputes', icon: AlertTriangle },
  { label: 'Support AI', path: '/portal/help', icon: HelpCircle },
  { label: 'Profile Settings', path: '/portal/profile', icon: UserIcon },
];

export const CustomerLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user] = useState(authService.getCurrentUser());

  const handleSwitchToAdmin = () => {
    authService.switchRole('admin');
    navigate('/admin/overview');
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/auth/login');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#08090a] font-sans text-slate-100 selection:bg-violet-600 selection:text-white">
      {/* Customer Sidebar */}
      <aside className="flex w-64 flex-col border-r border-white/[0.08] bg-[#0a0c10] z-30 select-none">
        {/* Customer Header */}
        <div className="flex h-16 items-center gap-3 px-6 border-b border-white/[0.08]">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 text-white font-bold text-sm shadow-glow-sm border border-violet-400/30">
            V
          </div>
          <div>
            <span className="font-bold text-white tracking-tight text-sm leading-none block">
              VERISUB
            </span>
            <p className="text-[10px] font-mono uppercase tracking-wider text-violet-400 mt-1">
              Customer Portal
            </p>
          </div>
        </div>

        {/* Customer Nav Links */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            My Account
          </p>
          {CUSTOMER_NAV.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

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
              >
                <Icon
                  className={cn(
                    'h-4 w-4 shrink-0 transition-colors',
                    isActive ? 'text-violet-400' : 'text-slate-500 group-hover:text-slate-300'
                  )}
                />
                <span className="truncate tracking-wide">{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Quick Return to Console Button */}
        <div className="p-3 border-t border-white/[0.08] space-y-2">
          <button
            onClick={handleSwitchToAdmin}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#141824] border border-white/[0.08] px-3 py-2 text-xs font-medium text-slate-200 hover:bg-violet-600 hover:text-white transition-all shadow-sm"
          >
            <ArrowLeftRight className="h-3.5 w-3.5 text-violet-400" />
            Switch to Admin Console
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden bg-[#08090a]">
        <header className="flex h-16 items-center justify-between border-b border-white/[0.08] bg-[#08090a]/90 px-8 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Account:</span>
            <span className="text-xs font-semibold text-white font-mono bg-white/[0.04] px-2.5 py-1 rounded-md border border-white/[0.06]">
              {user?.organization_name || 'TechCorp Global Solutions'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs font-semibold text-white">{user?.full_name}</p>
              <p className="text-[10px] text-slate-400 font-mono">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-rose-400 transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#08090a]">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
