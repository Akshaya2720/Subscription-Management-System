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
    <div className="flex items-center gap-1.5 p-1 rounded-full bg-[#e8e8ed]/80 border border-black/[0.05] overflow-x-auto select-none no-scrollbar w-fit max-w-full mb-2">
      {items.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) =>
            cn(
              'rounded-full px-3.5 py-1.5 text-xs font-medium transition-all duration-150 flex items-center gap-2 shrink-0 select-none',
              isActive
                ? 'bg-white text-[#1d1d1f] font-semibold shadow-xs'
                : 'text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-black/[0.04]'
            )
          }
        >
          {tab.icon}
          <span>{tab.label}</span>
          {tab.badge && (
            <span className="rounded-full bg-black/[0.06] px-1.5 py-0.2 text-[10px] font-mono text-[#1d1d1f]">
              {tab.badge}
            </span>
          )}
        </NavLink>
      ))}
    </div>
  );
};
