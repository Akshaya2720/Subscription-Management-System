import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../utils';

export interface SubNavTabItem {
  label: string;
  path: string;
  badge?: string;
}

export const SubNavTabs: React.FC<{ items: SubNavTabItem[] }> = ({ items }) => {
  return (
    <div className="flex items-center gap-1.5 border-b border-white/[0.08] pb-2.5 text-xs font-medium overflow-x-auto">
      {items.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) =>
            cn(
              'rounded-lg px-3 py-1.5 transition-all select-none flex items-center gap-1.5 shrink-0',
              isActive
                ? 'bg-violet-600/20 text-violet-300 border border-violet-500/30 font-semibold shadow-[0_0_10px_rgba(139,92,246,0.2)]'
                : 'text-slate-400 hover:text-white hover:bg-white/[0.04] border border-transparent'
            )
          }
        >
          <span>{tab.label}</span>
          {tab.badge && (
            <span className="rounded-full bg-white/[0.08] px-1.5 py-0.2 text-[9px] font-mono text-slate-300">
              {tab.badge}
            </span>
          )}
        </NavLink>
      ))}
    </div>
  );
};
