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
      'bg-white/[0.08] text-slate-300 border-white/[0.1] backdrop-blur-sm',
    success:
      'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 backdrop-blur-sm',
    warning:
      'bg-amber-500/15 text-amber-300 border-amber-500/30 backdrop-blur-sm',
    danger:
      'bg-rose-500/15 text-rose-300 border-rose-500/30 backdrop-blur-sm',
    info:
      'bg-blue-500/15 text-blue-300 border-blue-500/30 backdrop-blur-sm',
    purple:
      'bg-purple-500/15 text-purple-300 border-purple-500/30 backdrop-blur-sm',
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
