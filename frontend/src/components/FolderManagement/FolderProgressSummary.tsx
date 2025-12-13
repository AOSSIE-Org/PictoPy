import React from 'react';
import { CheckCircle2, Loader2, Clock } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { FolderStats } from '@/utils/folderUtils';

interface FolderProgressSummaryProps {
  stats: FolderStats;
}

/**
 * Displays overall AI tagging progress summary
 */
export const FolderProgressSummary: React.FC<FolderProgressSummaryProps> = ({
  stats,
}) => {
  const { total, completed, inProgress, pending, overallPercentage } = stats;

  if (total === 0) return null;

  const foldersWithTagging = completed + inProgress;

  return (
    <div className="bg-muted/50 mb-4 rounded-lg p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">AI Tagging Progress</h3>
        <span className="text-muted-foreground text-sm">
          {foldersWithTagging}/{total} folders enabled
        </span>
      </div>

      <Progress
        value={overallPercentage}
        className="mb-3 h-2"
        indicatorClassName={
          overallPercentage >= 100 ? 'bg-green-500' : 'bg-blue-500'
        }
      />

      <div className="flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-4 w-4 text-green-500" />
          <span className="text-muted-foreground">Completed:</span>
          <span className="font-medium">{completed}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Loader2 className="h-4 w-4 text-blue-500" />
          <span className="text-muted-foreground">In Progress:</span>
          <span className="font-medium">{inProgress}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Clock className="h-4 w-4 text-gray-400" />
          <span className="text-muted-foreground">Pending:</span>
          <span className="font-medium">{pending}</span>
        </div>
      </div>
    </div>
  );
};

export default FolderProgressSummary;
