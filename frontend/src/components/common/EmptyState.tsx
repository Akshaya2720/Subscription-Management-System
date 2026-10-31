import React from 'react';
import { cn } from '../../utils';
import { Button } from './Button';
import { FolderOpen } from 'lucide-react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
  className,
}) => (
  <div
    className={cn(
      'flex flex-col items-center justify-center rounded-2xl border border-dashed border-black/[0.1] bg-white p-12 text-center shadow-xs',
      className
    )}
  >
    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-[#6e6e73] mb-4">
      {icon || <FolderOpen className="h-7 w-7" />}
    </div>
    <h3 className="text-base font-semibold text-[#1d1d1f]">{title}</h3>
    <p className="mt-1 text-sm text-[#6e6e73] max-w-sm">{description}</p>
    {actionText && onAction && (
      <Button className="mt-5" onClick={onAction}>
        {actionText}
      </Button>
    )}
  </div>
);
