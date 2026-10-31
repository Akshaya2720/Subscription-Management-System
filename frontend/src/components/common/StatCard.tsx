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
  iconBg = 'bg-blue-500/10 border border-blue-500/25',
  iconColor = 'text-blue-400',
  badge,
  subtitle,
  className,
}) => {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;
  const isNeutral = change !== undefined && change === 0;

  return (
    <Card className={cn('relative overflow-hidden group hover:shadow-glow-blue transition-all duration-300', className)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold tracking-wider uppercase text-slate-400">
            {title}
          </p>
          <div className={cn('flex h-9 w-9 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110 shadow-sm', iconBg, iconColor)}>
            {icon}
          </div>
        </div>

        <div className="mt-3 flex items-baseline justify-between">
          <h3 className="text-2xl font-bold tracking-tight text-white font-sans">
            {value}
          </h3>
          {badge && (
            <span className="inline-flex items-center rounded-full bg-white/[0.08] border border-white/[0.1] px-2.5 py-0.5 text-[10px] font-medium text-slate-300">
              {badge}
            </span>
          )}
        </div>

        {change !== undefined && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs">
            <span
              className={cn(
                'inline-flex items-center gap-0.5 font-semibold text-xs',
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
