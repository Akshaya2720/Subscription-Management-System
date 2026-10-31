import React from 'react';
import { cn } from '../../utils';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const Table: React.FC<React.HTMLAttributes<HTMLTableElement>> = ({
  className,
  ...props
}) => (
  <div className="w-full overflow-x-auto rounded-xl border border-white/[0.08] bg-[#0e1117]/90 shadow-sm backdrop-blur-sm">
    <table className={cn('w-full caption-bottom text-xs', className)} {...props} />
  </div>
);

export const TableHeader: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <thead
    className={cn('bg-[#131722]/80 border-b border-white/[0.06]', className)}
    {...props}
  />
);

export const TableBody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <tbody className={cn('[&_tr:last-child]:border-0 divide-y divide-white/[0.04]', className)} {...props} />
);

export const TableRow: React.FC<React.HTMLAttributes<HTMLTableRowElement>> = ({
  className,
  ...props
}) => (
  <tr
    className={cn(
      'transition-colors hover:bg-white/[0.03] text-left text-slate-300',
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
      'h-10 px-4 text-left align-middle text-[11px] font-semibold tracking-wider text-slate-400 uppercase select-none',
      className
    )}
    {...props}
  />
);

export const TableCell: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  className,
  ...props
}) => (
  <td
    className={cn('p-4 align-middle text-slate-300 font-normal', className)}
    {...props}
  />
);

export const TableFooter: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <tfoot
    className={cn('border-t border-white/[0.06] bg-[#121620]/60 font-medium text-slate-300', className)}
    {...props}
  />
);

export interface TableEmptyProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  actionText?: string;
  onAction?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
  colSpan?: number;
}

export const TableEmpty: React.FC<TableEmptyProps> = ({
  title = 'No records found',
  description = 'There are no items to display matching the current criteria.',
  icon,
  actionText,
  onAction,
  action,
  colSpan = 100,
}) => {
  const buttonLabel = actionText || action?.label;
  const buttonClick = onAction || action?.onClick;

  return (
    <tbody>
      <tr>
        <td colSpan={colSpan} className="py-12 text-center">
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/[0.04] text-slate-500 border border-white/[0.06]">
              {icon || <Inbox className="h-6 w-6" />}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-200">{title}</p>
              <p className="text-xs text-slate-500 max-w-sm">{description}</p>
            </div>
            {buttonLabel && buttonClick && (
              <Button size="sm" variant="outline" onClick={buttonClick} className="mt-2">
                {buttonLabel}
              </Button>
            )}
          </div>
        </td>
      </tr>
    </tbody>
  );
};

export const TableEmptyState = TableEmpty;

export interface TableLoadingProps {
  columnsCount?: number;
  rowsCount?: number;
  colSpan?: number;
}

export const TableLoading: React.FC<TableLoadingProps> = ({
  columnsCount = 6,
  rowsCount = 3,
  colSpan,
}) => (
  <tbody>
    <tr>
      <td colSpan={colSpan || columnsCount} className="py-12 text-center">
        <div className="flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="h-6 w-6 animate-spin text-violet-400" />
          <p className="text-xs text-slate-400 font-mono">Querying ledger telemetry...</p>
        </div>
      </td>
    </tr>
  </tbody>
);

export const TableLoadingState = TableLoading;

export const TableErrorState: React.FC<{
  colSpan?: number;
  message?: string;
  onRetry?: () => void;
}> = ({ colSpan = 6, message = 'Failed to load data from backend API.', onRetry }) => (
  <tbody>
    <tr>
      <td colSpan={colSpan} className="py-10 text-center">
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-5 w-5" />
          </div>
          <p className="text-xs font-medium text-rose-400">{message}</p>
          {onRetry && (
            <Button size="sm" variant="outline" onClick={onRetry} leftIcon={<RefreshCw className="h-3 w-3" />}>
              Retry Request
            </Button>
          )}
        </div>
      </td>
    </tr>
  </tbody>
);
