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
  { label: 'Dashboard', path: '/portal/dashboard', icon: LayoutDashboard },
  { label: 'My Subscriptions', path: '/portal/subscriptions', icon: Repeat },
  { label: 'Invoices', path: '/portal/invoices', icon: Receipt },
  { label: 'Payment History', path: '/portal/payments', icon: CreditCard },
  { label: 'Service History', path: '/portal/services', icon: Activity },
  { label: 'Disputes', path: '/portal/disputes', icon: AlertTriangle },
  { label: 'Help Assistant', path: '/portal/help', icon: HelpCircle },
  { label: 'Profile', path: '/portal/profile', icon: UserIcon },
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
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100">
      {/* Customer Sidebar */}
      <aside className="flex w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 z-30 select-none">
        {/* Customer Header */}
        <div className="flex h-16 items-center gap-3 px-6 border-b border-slate-100 dark:border-slate-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white font-black text-base shadow-sm">
            V
          </div>
          <div>
            <span className="font-extrabold text-slate-900 tracking-tight text-base leading-none dark:text-white">
              VERISUB
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400 mt-0.5">
              Customer Portal
            </p>
          </div>
        </div>

        {/* Company Badge */}
        <div className="m-3 rounded-xl bg-slate-50 p-3 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Building className="h-4 w-4 text-brand-600" />
            <div className="truncate">
              <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                {user?.organization_name || 'Acme Technologies'}
              </p>
              <p className="text-[10px] text-slate-500">Active Customer Account</p>
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {CUSTOMER_NAV.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-100'
                )}
              >
                <Icon
                  className={cn(
                    'h-4 w-4 shrink-0',
                    isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400'
                  )}
                />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Role Quick Switcher & Logout */}
        <div className="p-3 border-t border-slate-100 dark:border-slate-800 space-y-1">
          <button
            onClick={handleSwitchToAdmin}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            <ArrowLeftRight className="h-3.5 w-3.5 text-brand-600" />
            Switch to Admin View
          </button>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Customer Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8 dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-base font-bold text-slate-900 dark:text-white capitalize">
            Customer Self-Service Hub
          </h1>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">Logged in as:</span>
            <span className="text-xs font-semibold text-slate-900 dark:text-white">
              {user?.email}
            </span>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
