import React from 'react';
import { Loader2, X } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export interface BackgroundTaskAlertProps {
  title: string;
  description?: string;
  /** Progress 0-100; omit for indeterminate tasks (spinner only, no bar) */
  percentage?: number;
  /** Renders a dismiss button when provided */
  onDismiss?: () => void;
  /** Extra classes for the outer fixed-position container */
  className?: string;
}

/**
 * Generic floating alert for long-running background work. Purely
 * presentational — pair it with a status hook that decides when and what.
 */
export const BackgroundTaskAlert: React.FC<BackgroundTaskAlertProps> = ({
  title,
  description,
  percentage,
  onDismiss,
  className,
}) => {
  return (
    <div
      className={cn(
        'fixed right-4 bottom-4 z-50 w-96 max-w-[calc(100vw-2rem)]',
        className,
      )}
    >
      <Alert className="shadow-lg" role="status" aria-live="polite">
        <Loader2 className="animate-spin text-blue-500" />
        <AlertTitle className={onDismiss ? 'pr-6' : undefined}>
          {title}
        </AlertTitle>
        <AlertDescription className="w-full">
          {description && <span>{description}</span>}
          {percentage !== undefined && (
            <div className="flex w-full items-center gap-2">
              <Progress
                value={percentage}
                className="bg-muted h-1.5 flex-1"
                indicatorClassName="bg-blue-500"
              />
              <span className="text-muted-foreground text-xs tabular-nums">
                {Math.floor(percentage)}%
              </span>
            </div>
          )}
        </AlertDescription>
        {onDismiss && (
          <button
            type="button"
            aria-label="Dismiss notification"
            className="text-muted-foreground hover:text-foreground absolute top-3 right-3 cursor-pointer"
            onClick={onDismiss}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </Alert>
    </div>
  );
};
