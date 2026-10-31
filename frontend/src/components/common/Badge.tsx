import React from 'react';
import { cn } from '../../utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const variants = {
    default:
      'bg-slate-100 text-[#1d1d1f] border-slate-200/80',
    success:
      'bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold',
    warning:
      'bg-amber-50 text-amber-900 border-amber-200 font-semibold',
    danger:
      'bg-rose-50 text-rose-800 border-rose-200 font-semibold',
    info:
      'bg-blue-50 text-[#0071e3] border-blue-200 font-semibold',
    purple:
      'bg-purple-50 text-purple-800 border-purple-200 font-semibold',
  };

  const sizes = {
    sm: 'text-[10px] px-2.5 py-0.5 rounded-full font-medium',
    md: 'text-xs px-3 py-1 rounded-full font-medium',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium border leading-none tracking-wide select-none',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
