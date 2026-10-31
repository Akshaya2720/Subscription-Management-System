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
      'bg-zinc-800/80 text-zinc-300 border-zinc-700/60',
    success:
      'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning:
      'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger:
      'bg-rose-500/10 text-rose-400 border-rose-500/30',
    info:
      'bg-sky-500/10 text-sky-400 border-sky-500/30',
    purple:
      'bg-violet-500/10 text-violet-300 border-violet-500/30',
  };

  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 rounded-full font-medium',
    md: 'text-xs px-2.5 py-0.5 rounded-full font-medium',
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
