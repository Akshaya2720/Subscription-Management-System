import React from 'react';
import { motion } from 'framer-motion';
import { Check, Clock, PlayCircle, PauseCircle, XCircle, FileText } from 'lucide-react';
import { cn } from '../../utils';
import { SubscriptionStatus } from '../../types';

export interface SubscriptionTimelineProps {
  currentStatus: SubscriptionStatus;
  className?: string;
}

const STAGES: {
  status: SubscriptionStatus;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}[] = [
  { status: 'draft', label: 'Draft', icon: FileText, description: 'Initial contract parameters' },
  { status: 'quotation', label: 'Quotation', icon: Clock, description: 'Pricing & SLA review' },
  { status: 'confirmed', label: 'Confirmed', icon: Check, description: 'Client approved order' },
  { status: 'active', label: 'Active', icon: PlayCircle, description: 'Delivering SLA & billing' },
  { status: 'closed', label: 'Closed', icon: XCircle, description: 'Terminated or completed' },
];

export const SubscriptionTimeline: React.FC<SubscriptionTimelineProps> = ({
  currentStatus,
  className,
}) => {
  const getStageIndex = (status: SubscriptionStatus) => {
    if (status === 'paused') return 3; // treated along with Active stage
    if (status === 'cancelled') return 4;
    return STAGES.findIndex((s) => s.status === status);
  };

  const currentIndex = getStageIndex(currentStatus);

  return (
    <div className={cn('w-full py-4', className)}>
      <div className="relative flex items-center justify-between">
        {/* Connecting Progress Line */}
        <div className="absolute left-6 right-6 top-5 -z-0 h-1 bg-slate-200">
          <motion.div
            className="h-full bg-[#0071e3]"
            initial={{ width: 0 }}
            animate={{
              width: currentIndex >= 0 ? `${(currentIndex / (STAGES.length - 1)) * 100}%` : '0%',
            }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
          />
        </div>

        {/* Step Nodes */}
        {STAGES.map((stage, idx) => {
          const isPassed = idx < currentIndex;
          const isCurrent = idx === currentIndex;
          const isPaused = currentStatus === 'paused' && isCurrent;
          const Icon = isPaused ? PauseCircle : stage.icon;

          return (
            <div key={stage.status} className="relative z-10 flex flex-col items-center">
              <motion.div
                initial={false}
                animate={{
                  scale: isCurrent ? 1.15 : 1,
                  backgroundColor: isCurrent
                    ? isPaused
                      ? '#f59e0b'
                      : '#0071e3'
                    : isPassed
                    ? '#10b981'
                    : '#ffffff',
                }}
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-full border-2 text-white shadow-2xs transition-colors',
                  isCurrent && 'ring-4 ring-blue-100',
                  !isPassed && !isCurrent && 'border-slate-300 text-[#86868b]'
                )}
              >
                {isPassed ? (
                  <Check className="h-5 w-5 text-white" />
                ) : (
                  <Icon
                    className={cn(
                      'h-5 w-5',
                      isCurrent ? 'text-white' : 'text-[#86868b]'
                    )}
                  />
                )}
              </motion.div>

              <div className="mt-2.5 text-center">
                <span
                  className={cn(
                    'block text-xs font-semibold',
                    isCurrent
                      ? isPaused
                        ? 'text-amber-700 font-bold'
                        : 'text-[#0071e3] font-bold'
                      : isPassed
                      ? 'text-[#1d1d1f]'
                      : 'text-[#86868b]'
                  )}
                >
                  {isPaused ? 'Paused' : stage.label}
                </span>
                <span className="hidden sm:block text-[11px] text-[#6e6e73]">
                  {stage.description}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
