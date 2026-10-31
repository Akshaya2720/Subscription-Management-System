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
      'inline-flex items-center justify-center font-medium rounded-full transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#0071e3]/30 disabled:opacity-50 disabled:pointer-events-none select-none active:scale-[0.98]';

    const variants = {
      primary:
        'bg-[#0071e3] text-white hover:bg-[#0077ed] active:bg-[#0062c4] shadow-xs font-semibold',
      secondary:
        'bg-[#e8e8ed] text-[#1d1d1f] hover:bg-[#dcdce2] active:bg-[#d0d0d8] font-medium',
      outline:
        'border border-[#d2d2d7] bg-white text-[#1d1d1f] hover:bg-[#f5f5f7] active:bg-[#e8e8ed] shadow-2xs font-medium',
      ghost:
        'text-[#1d1d1f] hover:bg-black/[0.05]',
      danger:
        'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 shadow-xs font-medium',
    };

    const sizes = {
      sm: 'text-xs px-3.5 py-1.5 gap-1.5',
      md: 'text-xs px-4 py-2 gap-2',
      lg: 'text-sm px-5 py-2.5 gap-2.5',
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
