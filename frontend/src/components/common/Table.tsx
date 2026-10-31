import React from 'react';
import { cn } from '../../utils';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const Table: React.FC<React.HTMLAttributes<HTMLTableElement>> = ({
  className,
  ...props
}) => (
  <div className="w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <table className={cn('w-full caption-bottom text-sm', className)} {...props} />
  </div>
);

export const TableHeader: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <thead
    className={cn('bg-slate-50/75 border-b border-slate-200 dark:bg-slate-800/40 dark:border-slate-800', className)}
    {...props}
  />
);

export const TableBody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <tbody className={cn('[&_tr:last-child]:border-0 divide-y divide-slate-100 dark:divide-slate-800/60', className)} {...props} />
);

export const TableRow: React.FC<React.HTMLAttributes<HTMLTableRowElement>> = ({
  className,
  ...props
}) => (
  <tr
    className={cn(
      'transition-colors hover:bg-slate-50/70 dark:hover:bg-slate-800/40 text-left',
      className
    )}
    {...props}
  />
);

export const TableHead: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({
  className,
  ...props
}) => (
  <th
    className={cn(
      'h-11 px-4 text-left align-middle text-xs font-semibold tracking-wider text-slate-500 uppercase dark:text-slate-400 select-none',
      className
    )}
    {...props}
  />
);

export const TableCell: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  className,
  ...props
}) => (
  <td className={cn('p-4 align-middle text-slate-700 dark:text-slate-300', className)} {...props} />
);

export const TableLoading: React.FC<{ columnsCount?: number; rowsCount?: number }> = ({
  columnsCount = 5,
  rowsCount = 4,
}) => (
  <tbody>
    {Array.from({ length: rowsCount }).map((_, r) => (
      <tr key={r} className="border-b border-slate-100 dark:border-slate-800/60 animate-pulse">
        {Array.from({ length: columnsCount }).map((_, c) => (
          <td key={c} className="p-4">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full" />
          </td>
        ))}
      </tr>
    ))}
  </tbody>
);

export const TableEmpty: React.FC<{
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  colSpan?: number;
}> = ({
  title = 'No records found',
  description = 'There are no items matching your criteria or database is currently empty.',
  actionText,
  onAction,
  colSpan = 6,
}) => (
  <tbody>
    <tr>
      <td colSpan={colSpan} className="py-16 text-center">
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400">
            <Inbox className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm">{description}</p>
          </div>
          {actionText && onAction && (
            <Button size="sm" variant="outline" onClick={onAction}>
              {actionText}
            </Button>
          )}
        </div>
      </td>
    </tr>
  </tbody>
);

export const TableError: React.FC<{
  message?: string;
  onRetry?: () => void;
  colSpan?: number;
}> = ({
  message = 'Failed to load records from backend server.',
  onRetry,
  colSpan = 6,
}) => (
  <tbody>
    <tr>
      <td colSpan={colSpan} className="py-12 text-center">
        <div className="flex flex-col items-center justify-center space-y-3 text-rose-600 dark:text-rose-400">
          <AlertCircle className="h-8 w-8" />
          <p className="text-sm font-medium">{message}</p>
          {onRetry && (
            <Button size="sm" variant="outline" onClick={onRetry} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
              Retry Connection
            </Button>
          )}
        </div>
      </td>
    </tr>
  </tbody>
);
