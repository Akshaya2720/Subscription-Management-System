import React from 'react';
import { Card, CardContent } from './Card';
import { cn } from '../../utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  iconBg?: string;
  iconColor?: string;
  badge?: string;
  subtitle?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeLabel = 'vs last month',
  icon,
  iconBg = 'bg-brand-50 dark:bg-brand-950/60',
  iconColor = 'text-brand-600 dark:text-brand-400',
  badge,
  subtitle,
  className,
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;
  const isNeutral = change !== undefined && change === 0;

  return (
    <Card className={cn('relative overflow-hidden hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </p>
          <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', iconBg, iconColor)}>
            {icon}
          </div>
        </div>

        <div className="mt-3 flex items-baseline justify-between">
          <h3 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {value}
          </h3>
          {badge && (
            <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {badge}
            </span>
          )}
        </div>

        {change !== undefined && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs">
            <span
              className={cn(
                'inline-flex items-center font-semibold',
                isPositive && 'text-emerald-600 dark:text-emerald-400',
                isNegative && 'text-rose-600 dark:text-rose-400',
                isNeutral && 'text-slate-500'
              )}
            >
              {isPositive && <TrendingUp className="mr-0.5 h-3.5 w-3.5" />}
              {isNegative && <TrendingDown className="mr-0.5 h-3.5 w-3.5" />}
              {isNeutral && <Minus className="mr-0.5 h-3.5 w-3.5" />}
              {isPositive ? `+${change}%` : `${change}%`}
            </span>
            <span className="text-slate-500 dark:text-slate-400">{changeLabel}</span>
          </div>
        )}

        {subtitle && (
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
};
