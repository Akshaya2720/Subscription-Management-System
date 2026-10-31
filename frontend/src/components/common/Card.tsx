import React from 'react';
import { cn } from '../../utils';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => (
  <div
    className={cn(
      'rounded-2xl border border-black/[0.07] bg-white text-[#1d1d1f] shadow-[0_2px_12px_rgba(0,0,0,0.03)] transition-all duration-200 hover:border-black/[0.12] hover:shadow-[0_4px_20px_rgba(0,0,0,0.05)]',
      className
    )}
    {...props}
  />
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => (
  <div
    className={cn('flex flex-col space-y-1 p-5 sm:p-6 border-b border-black/[0.05]', className)}
    {...props}
  />
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  ...props
}) => (
  <h3
    className={cn('font-semibold leading-none tracking-tight text-[#1d1d1f] text-base sm:text-lg', className)}
    {...props}
  />
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  ...props
}) => (
  <p
    className={cn('text-xs text-[#6e6e73] font-normal leading-relaxed', className)}
    {...props}
  />
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => <div className={cn('p-5 sm:p-6', className)} {...props} />;

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => (
  <div
    className={cn('flex items-center p-5 sm:p-6 pt-0 border-t border-black/[0.05] mt-4', className)}
    {...props}
  />
);
