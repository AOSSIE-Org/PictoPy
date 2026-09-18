import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

interface DetailPageHeaderProps {
  backLabel: string;
  onBack: () => void;
  title: string;
  description?: string;
  meta?: React.ReactNode;
  actions?: React.ReactNode;
}

export const DetailPageHeader = ({
  backLabel,
  onBack,
  title,
  description,
  meta,
  actions,
}: DetailPageHeaderProps) => (
  <div className="mb-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <Button
        variant="outline"
        onClick={onBack}
        className="flex cursor-pointer items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        {backLabel}
      </Button>
      {actions && (
        <div className="flex flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
    <div className="mt-4">
      <div>
        <div className="flex flex-wrap items-baseline gap-2">
          <h1 className="text-2xl font-bold">{title}</h1>
          {meta && (
            <div className="text-muted-foreground text-sm whitespace-nowrap">
              {meta}
            </div>
          )}
        </div>
        {description && (
          <p className="text-muted-foreground text-sm">{description}</p>
        )}
      </div>
    </div>
  </div>
);
