import React, { ButtonHTMLAttributes } from 'react';
import { cn } from '../../utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#08090a] disabled:opacity-50 disabled:pointer-events-none select-none active:scale-[0.99]';

    const variants = {
      primary:
        'bg-violet-600 text-white hover:bg-violet-500 active:bg-violet-700 focus:ring-violet-500 shadow-glow-sm border border-violet-400/20',
      secondary:
        'bg-[#161a24] text-slate-200 border border-white/[0.09] hover:bg-[#1e2333] hover:text-white focus:ring-slate-500',
      outline:
        'border border-white/[0.12] bg-transparent text-slate-300 hover:bg-white/[0.05] hover:text-white hover:border-white/[0.2] focus:ring-violet-500',
      ghost:
        'text-slate-400 hover:bg-white/[0.06] hover:text-slate-200 focus:ring-slate-500',
      danger:
        'bg-rose-600/90 text-white hover:bg-rose-500 active:bg-rose-700 focus:ring-rose-500 border border-rose-500/30 shadow-glow-rose',
    };

    const sizes = {
      sm: 'text-xs px-2.5 py-1.5 gap-1.5',
      md: 'text-xs font-semibold px-3.5 py-2 gap-2',
      lg: 'text-sm font-semibold px-4.5 py-2.5 gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
