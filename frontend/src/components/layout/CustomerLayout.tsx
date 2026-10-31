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
  ArrowLeftRight,
} from 'lucide-react';
import { cn } from '../../utils';
import { authService } from '../../services/auth';

const CUSTOMER_NAV = [
  { label: 'Overview', path: '/portal/dashboard', icon: LayoutDashboard },
  { label: 'Subscriptions', path: '/portal/subscriptions', icon: Repeat },
  { label: 'Invoices', path: '/portal/invoices', icon: Receipt },
  { label: 'Payments', path: '/portal/payments', icon: CreditCard },
  { label: 'Telemetry', path: '/portal/services', icon: Activity },
  { label: 'Disputes & SLA', path: '/portal/disputes', icon: AlertTriangle },
  { label: 'Support AI', path: '/portal/help', icon: HelpCircle },
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
    <div className="min-h-screen w-screen overflow-x-hidden font-sans text-slate-100 selection:bg-blue-600 selection:text-white flex flex-col">
      {/* Supaste Floating Dynamic Island for Customer Portal */}
      <div className="sticky top-3 z-40 w-full px-4 sm:px-6 mb-4">
        <header className="mx-auto flex h-14 max-w-7xl items-center justify-between rounded-full border border-white/[0.13] bg-[#0c1220]/85 px-4 sm:px-5 backdrop-blur-2xl shadow-island">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-cyan-500 text-white font-black text-xs shadow-glow-blue border border-white/20">
              V
            </div>
            <div>
              <span className="font-bold text-white tracking-tight text-sm leading-none block">
                VERISUB
              </span>
              <p className="text-[9px] font-mono uppercase tracking-wider text-blue-400 mt-0.5">
                Client Hub
              </p>
            </div>
          </div>

          {/* Navigation Pills */}
          <nav className="hidden lg:flex items-center gap-1">
            {CUSTOMER_NAV.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

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
                </NavLink>
              );
            })}
          </nav>

          {/* Right Action: Return to Admin Console & Profile */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSwitchToAdmin}
              className="flex items-center gap-1.5 rounded-full bg-white/[0.08] border border-white/[0.12] px-3 py-1 text-xs font-medium text-slate-200 hover:bg-blue-600 hover:text-white transition-all shadow-sm"
            >
              <ArrowLeftRight className="h-3 w-3 text-blue-400" />
              <span className="hidden sm:inline">Admin Console</span>
            </button>

            <button
              onClick={handleLogout}
              className="rounded-full p-2 text-slate-400 hover:bg-white/[0.08] hover:text-rose-400 transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
      </div>

      {/* Main Content Viewport */}
      <main className="flex-1 px-4 sm:px-6 pb-12">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
