import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../utils';

export interface SubNavTabItem {
  label: string;
  path: string;
  badge?: string;
  icon?: React.ReactNode;
}

export const SubNavTabs: React.FC<{ items: SubNavTabItem[] }> = ({ items }) => {
  return (
    <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3 text-xs font-medium overflow-x-auto select-none no-scrollbar">
      {items.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) =>
            cn(
              'rounded-full px-3.5 py-1.5 transition-all duration-200 flex items-center gap-2 shrink-0 backdrop-blur-md',
              isActive
                ? 'bg-blue-600/25 text-blue-300 border border-blue-500/40 font-semibold shadow-[0_0_16px_rgba(59,130,246,0.3)]'
                : 'bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08] border border-white/[0.07]'
            )
          }
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.badge && (
            <span className="rounded-full bg-white/[0.1] px-1.5 py-0.2 text-[10px] font-mono text-slate-300">
              {tab.badge}
            </span>
          )}
        </NavLink>
      ))}
    </div>
  );
};
