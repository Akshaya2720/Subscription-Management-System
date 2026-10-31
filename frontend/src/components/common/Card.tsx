import React from 'react';
import { cn } from '../../utils';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => (
  <div
    className={cn(
      'rounded-2xl border border-white/[0.09] bg-[#0d1424]/70 backdrop-blur-2xl text-slate-100 shadow-glass-card transition-all duration-200 hover:border-blue-500/30',
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
    className={cn('flex flex-col space-y-1.5 p-5 sm:p-6 border-b border-white/[0.06]', className)}
    {...props}
  />
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  ...props
}) => (
  <h3
    className={cn('font-semibold leading-none tracking-tight text-white text-base', className)}
    {...props}
  />
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  ...props
}) => (
  <p
    className={cn('text-xs text-slate-400 font-normal', className)}
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
    className={cn('flex items-center p-5 sm:p-6 pt-0 border-t border-white/[0.06] mt-5', className)}
    {...props}
  />
);
