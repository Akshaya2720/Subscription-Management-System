import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
} from 'lucide-react';
import { User, UserRole } from '../../types';
import { authService } from '../../services/auth';

interface TopNavProps {
  user: User | null;
  onRoleChange: (role: UserRole) => void;
}

export const TopNav: React.FC<TopNavProps> = ({ user, onRoleChange }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [orgOpen, setOrgOpen] = useState(false);

  // Generate breadcrumbs from pathname
  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentTitle = pathParts[1]
    ? pathParts[1].replace('-', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Overview';

  const handleLogout = () => {
    authService.logout();
    navigate('/auth/login');
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-6 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/95">
      {/* Left: Breadcrumbs & Quick Search */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          <span className="capitalize">{pathParts[0] || 'App'}</span>
          <span>/</span>
          <span className="font-semibold text-slate-900 dark:text-white capitalize">
            {currentTitle}
          </span>
        </div>

        {/* Global Search Bar */}
        <div className="hidden md:flex relative items-center">
          <Search className="pointer-events-none absolute left-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search subscriptions, invoices, customers..."
            className="w-72 rounded-lg border border-slate-200 bg-slate-50/80 pl-9 pr-4 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:bg-slate-900"
          />
        </div>
      </div>

      {/* Right Controls: Role Simulation Switcher, Notifications, Profile */}
      <div className="flex items-center gap-3">
        {/* Dynamic Role Switcher (For Evaluation & Multi-Persona Verification) */}
        <div className="hidden sm:flex items-center rounded-lg bg-slate-100 p-1 dark:bg-slate-800 text-xs font-semibold">
          <button
            onClick={() => {
              onRoleChange('admin');
              navigate('/admin/overview');
            }}
            className={`rounded-md px-2.5 py-1 transition-all ${
              user?.role === 'admin'
                ? 'bg-white text-slate-900 shadow-xs dark:bg-slate-700 dark:text-white'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400'
            }`}
          >
            Admin
          </button>
          <button
            onClick={() => {
              onRoleChange('staff');
              navigate('/admin/overview');
            }}
            className={`rounded-md px-2.5 py-1 transition-all ${
              user?.role === 'staff'
                ? 'bg-white text-slate-900 shadow-xs dark:bg-slate-700 dark:text-white'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400'
            }`}
          >
            Staff
          </button>
          <button
            onClick={() => {
              onRoleChange('customer');
              navigate('/portal/dashboard');
            }}
            className={`rounded-md px-2.5 py-1 transition-all ${
              user?.role === 'customer'
                ? 'bg-brand-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400'
            }`}
          >
            Customer Portal
          </button>
        </div>

        {/* Organization Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOrgOpen(!orgOpen)}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <Building className="h-3.5 w-3.5 text-brand-600" />
            <span className="max-w-[120px] truncate">{user?.organization_name || 'Acme Inc'}</span>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>

          {orgOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-slate-900 z-50">
              <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Organizations
              </div>
              <button
                onClick={() => setOrgOpen(false)}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-slate-900 hover:bg-slate-50 dark:text-white dark:hover:bg-slate-800"
              >
                <span>{user?.organization_name || 'Verisub Enterprise'}</span>
                <CheckCircle2 className="h-3.5 w-3.5 text-brand-600" />
              </button>
            </div>
          )}
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white dark:ring-slate-900" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-800 dark:bg-slate-900 z-50">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                <span className="text-xs font-semibold text-slate-900 dark:text-white">
                  Notifications & Alerts
                </span>
                <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-700">
                  2 New
                </span>
              </div>
              <div className="mt-2 space-y-2">
                <div className="rounded-lg bg-rose-50/60 p-2.5 dark:bg-rose-950/30">
                  <div className="flex items-center gap-2 text-xs font-semibold text-rose-800 dark:text-rose-300">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    SLA Violation Alert
                  </div>
                  <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
                    Sub SUB-2026-0412 has 168 min recorded downtime. $249.90 credit proposed.
                  </p>
                </div>
                <div className="rounded-lg bg-indigo-50/60 p-2.5 dark:bg-indigo-950/30">
                  <div className="flex items-center gap-2 text-xs font-semibold text-brand-800 dark:text-brand-300">
                    <Sparkles className="h-3.5 w-3.5" />
                    AI Anomaly Report
                  </div>
                  <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
                    Unexpected manual discount flagged on Quotation QUO-2026-0098.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white uppercase">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div className="hidden lg:block text-left leading-tight">
              <p className="text-xs font-semibold text-slate-900 dark:text-white">
                {user?.full_name || 'Admin'}
              </p>
              <p className="text-[10px] text-slate-500 capitalize">{user?.role || 'admin'}</p>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-slate-900 z-50">
              <div className="border-b border-slate-100 px-3 py-2 dark:border-slate-800">
                <p className="text-xs font-semibold text-slate-900 dark:text-white">
                  {user?.full_name}
                </p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    navigate('/admin/settings');
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  <UserIcon className="h-3.5 w-3.5 text-slate-400" />
                  Account Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
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
  );
};
