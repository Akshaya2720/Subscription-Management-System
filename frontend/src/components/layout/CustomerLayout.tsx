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
    <div className="min-h-screen w-screen overflow-x-hidden font-sans text-[#1d1d1f] bg-[#f5f5f7] selection:bg-[#0071e3] selection:text-white flex flex-col">
      {/* Apple Store Header for Customer Portal */}
      <div className="sticky top-0 z-40 w-full border-b border-black/[0.08] bg-white/80 backdrop-blur-xl">
        <header className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#1d1d1f] text-white font-bold text-xs shadow-2xs">
              V
            </div>
            <div>
              <span className="font-bold text-[#1d1d1f] tracking-tight text-sm leading-none block">
                VERISUB
              </span>
              <p className="text-[9px] font-mono uppercase tracking-wider text-[#0071e3] mt-0.5 font-semibold">
                Client Portal
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
                    'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-150 select-none',
                    isActive
                      ? 'bg-black/[0.08] text-[#1d1d1f] font-semibold'
                      : 'text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.04]'
                  )}
                >
                  <Icon className={cn('h-3.5 w-3.5', isActive ? 'text-[#0071e3]' : 'text-[#86868b]')} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Right Action: Return to Admin Console & Sign Out */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSwitchToAdmin}
              className="flex items-center gap-1.5 rounded-full bg-white border border-black/[0.08] px-3.5 py-1.5 text-xs font-medium text-[#1d1d1f] hover:bg-[#f5f5f7] transition-all shadow-2xs"
            >
              <ArrowLeftRight className="h-3 w-3 text-[#0071e3]" />
              <span className="hidden sm:inline">Admin Console</span>
            </button>

            <button
              onClick={handleLogout}
              className="rounded-full p-2 text-[#6e6e73] hover:bg-black/[0.05] hover:text-rose-600 transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
      </div>

      {/* Main Content Viewport */}
      <main className="flex-1 px-4 sm:px-6 pb-12 pt-4">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
