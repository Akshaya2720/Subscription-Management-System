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
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-white/[0.08] bg-[#08090a]/90 px-6 backdrop-blur-md">
      {/* Left: Breadcrumbs & Quick Search */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
          <span className="capitalize text-slate-500">{pathParts[0] || 'App'}</span>
          <span className="text-slate-600">/</span>
          <span className="font-semibold text-white capitalize">
            {currentTitle}
          </span>
        </div>

        {/* Global Search Bar */}
        <div className="hidden md:flex relative items-center">
          <Search className="pointer-events-none absolute left-3 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search subscriptions, invoices, telemetry... (⌘K)"
            className="w-80 rounded-lg border border-white/[0.08] bg-[#0e1117] pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-500 focus:border-violet-500 focus:bg-[#121622] focus:outline-none focus:ring-1 focus:ring-violet-500/30 transition-all font-sans"
          />
        </div>
      </div>

      {/* Right Controls: Role Simulation Switcher, Notifications, Profile */}
      <div className="flex items-center gap-3">
        {/* Dynamic Role Switcher (For Evaluation & Multi-Persona Verification) */}
        <div className="hidden sm:flex items-center rounded-lg bg-[#11141e] p-1 border border-white/[0.08] text-xs font-medium">
          <button
            onClick={() => {
              onRoleChange('admin');
              navigate('/admin/overview');
            }}
            className={`rounded-md px-2.5 py-1 transition-all ${
              user?.role === 'admin'
                ? 'bg-violet-600 text-white shadow-glow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200'
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
                ? 'bg-violet-600 text-white shadow-glow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200'
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
                ? 'bg-violet-600 text-white shadow-glow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Customer Portal
          </button>
        </div>

        {/* Organization Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOrgOpen(!orgOpen)}
            className="flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#0e1117] px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-[#141824] hover:text-white transition-colors"
          >
            <Building className="h-3.5 w-3.5 text-violet-400" />
            <span className="max-w-[120px] truncate">{user?.organization_name || 'Acme Inc'}</span>
            <ChevronDown className="h-3 w-3 text-slate-500" />
          </button>

          {orgOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-white/[0.1] bg-[#0e1117] p-2 shadow-2xl z-50">
              <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                Organizations
              </div>
              <button
                onClick={() => setOrgOpen(false)}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-white hover:bg-white/[0.06]"
              >
                <span>{user?.organization_name || 'Verisub Enterprise'}</span>
                <CheckCircle2 className="h-3.5 w-3.5 text-violet-400" />
              </button>
            </div>
          )}
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative rounded-lg p-2 text-slate-400 hover:bg-white/[0.06] hover:text-white transition-colors"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-[#08090a]" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-white/[0.1] bg-[#0e1117] p-3 shadow-2xl z-50">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                <span className="text-xs font-semibold text-white">
                  Telemetry & Anomaly Alerts
                </span>
                <span className="rounded-full bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 text-[10px] font-mono font-bold text-rose-400">
                  2 New
                </span>
              </div>
              <div className="mt-2.5 space-y-2">
                <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-2.5">
                  <div className="flex items-center gap-2 text-xs font-semibold text-rose-300">
                    <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
                    SLA Discrepancy Detected
                  </div>
                  <p className="mt-1 text-[11px] text-slate-400">
                    Sub SUB-2026-0412 has 168 min recorded downtime. $249.90 credit proposed.
                  </p>
                </div>
                <div className="rounded-lg bg-violet-500/10 border border-violet-500/20 p-2.5">
                  <div className="flex items-center gap-2 text-xs font-semibold text-violet-300">
                    <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                    AI Anomaly Report
                  </div>
                  <p className="mt-1 text-[11px] text-slate-400">
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
            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-white/[0.06] transition-colors"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 text-xs font-bold text-white uppercase border border-violet-400/30">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div className="hidden lg:block text-left leading-tight">
              <p className="text-xs font-semibold text-white">
                {user?.full_name || 'Admin'}
              </p>
              <p className="text-[10px] text-slate-400 capitalize">{user?.role || 'admin'}</p>
            </div>
            <ChevronDown className="h-3 w-3 text-slate-500" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border border-white/[0.1] bg-[#0e1117] p-2 shadow-2xl z-50">
              <div className="border-b border-white/[0.06] px-3 py-2">
                <p className="text-xs font-semibold text-white">
                  {user?.full_name}
                </p>
                <p className="text-[11px] text-slate-400 font-mono truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    navigate('/admin/settings');
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-300 hover:bg-white/[0.06] hover:text-white"
                >
                  <UserIcon className="h-3.5 w-3.5 text-slate-400" />
                  Account Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/10"
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
