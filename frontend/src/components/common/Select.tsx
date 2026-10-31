import React, { SelectHTMLAttributes } from 'react';
import { cn } from '../../utils';

export interface SelectOption {
  label: string;
  value: string | number;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, options, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-[11px] font-semibold uppercase tracking-wider text-slate-300"
          >
            {label}
          </label>
        )}
        <select
          id={selectId}
          ref={ref}
          className={cn(
            'block w-full rounded-lg border bg-[#090b10] px-3.5 py-2 text-xs text-white transition-colors focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500/30 disabled:cursor-not-allowed disabled:bg-slate-900/50 disabled:text-slate-500 border-white/[0.1]',
            error
              ? 'border-rose-500/60 text-rose-300 focus:border-rose-500 focus:ring-rose-500/30'
              : 'hover:border-white/[0.18]',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-[#0e1117] text-white">
              {opt.label}
            </option>
          ))}
        </select>
        {error && <p className="text-[11px] font-medium text-rose-400">{error}</p>}
        {helperText && !error && (
          <p className="text-[11px] text-slate-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
