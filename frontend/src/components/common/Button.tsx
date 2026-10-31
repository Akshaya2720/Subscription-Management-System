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
      'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-50 disabled:pointer-events-none select-none active:scale-[0.98]';

    const variants = {
      primary:
        'bg-blue-600 text-white hover:bg-blue-500 active:bg-blue-700 shadow-glow-blue border border-blue-400/30',
      secondary:
        'bg-white/[0.08] text-slate-100 border border-white/[0.12] hover:bg-white/[0.14] hover:text-white backdrop-blur-md',
      outline:
        'border border-white/[0.15] bg-transparent text-slate-300 hover:bg-white/[0.06] hover:text-white hover:border-white/[0.25]',
      ghost:
        'text-slate-400 hover:bg-white/[0.06] hover:text-white',
      danger:
        'bg-rose-600 text-white hover:bg-rose-500 active:bg-rose-700 border border-rose-500/30 shadow-[0_0_20px_rgba(244,63,94,0.3)]',
    };

    const sizes = {
      sm: 'text-xs px-3 py-1.5 gap-1.5',
      md: 'text-xs font-semibold px-4 py-2 gap-2',
      lg: 'text-sm font-semibold px-5 py-2.5 gap-2.5',
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
