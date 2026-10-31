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
            className="block text-[11px] font-semibold uppercase tracking-wider text-[#6e6e73]"
          >
            {label}
          </label>
        )}
        <select
          id={selectId}
          ref={ref}
          className={cn(
            'block w-full rounded-xl border border-[#d2d2d7] bg-white px-3 py-2 text-xs text-[#1d1d1f] transition-all focus:border-[#0071e3] focus:outline-none focus:ring-2 focus:ring-[#0071e3]/20 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400',
            error
              ? 'border-rose-400 text-rose-800 focus:border-rose-500 focus:ring-rose-200'
              : 'hover:border-[#a1a1a6]',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-white text-[#1d1d1f]">
              {opt.label}
            </option>
          ))}
        </select>
        {error && <p className="text-[11px] font-medium text-rose-600">{error}</p>}
        {helperText && !error && (
          <p className="text-[11px] text-[#6e6e73]">{helperText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
