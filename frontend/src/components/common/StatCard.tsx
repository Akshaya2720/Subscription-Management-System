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
  changeLabel = 'vs last period',
  icon,
  iconBg = 'bg-brand-500/10 border border-brand-500/20',
  iconColor = 'text-brand-400',
  badge,
  subtitle,
  className,
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;
  const isNeutral = change !== undefined && change === 0;

  return (
    <Card className={cn('relative overflow-hidden hover:border-brand-500/30 transition-all group', className)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-medium tracking-wide uppercase text-slate-400">
            {title}
          </p>
          <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg transition-transform group-hover:scale-105', iconBg, iconColor)}>
            {icon}
          </div>
        </div>

        <div className="mt-3 flex items-baseline justify-between">
          <h3 className="text-2xl font-bold tracking-tight text-white font-mono">
            {value}
          </h3>
          {badge && (
            <span className="inline-flex items-center rounded-full bg-white/[0.06] border border-white/[0.08] px-2 py-0.5 text-[10px] font-medium text-slate-300">
              {badge}
            </span>
          )}
        </div>

        {change !== undefined && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs">
            <span
              className={cn(
                'inline-flex items-center gap-0.5 font-medium',
                isPositive && 'text-emerald-400',
                isNegative && 'text-rose-400',
                isNeutral && 'text-slate-400'
              )}
            >
              {isPositive && <TrendingUp className="h-3.5 w-3.5" />}
              {isNegative && <TrendingDown className="h-3.5 w-3.5" />}
              {isNeutral && <Minus className="h-3.5 w-3.5" />}
              {change > 0 ? `+${change}%` : `${change}%`}
            </span>
            <span className="text-slate-500 text-[11px] truncate">{changeLabel}</span>
          </div>
        )}

        {subtitle && !change && (
          <p className="mt-2 text-xs text-slate-400 truncate">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
};
