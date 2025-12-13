import React from 'react';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

interface ProgressSummaryProps {
  totalFolders: number;
  completedFolders: number;
  inProgressFolders: number;
  pendingFolders: number;
}

export const ProgressSummary: React.FC<ProgressSummaryProps> = ({
  totalFolders,
  completedFolders,
  inProgressFolders,
  pendingFolders,
}) => {
  const completionPercentage =
    totalFolders > 0 ? Math.round((completedFolders / totalFolders) * 100) : 0;

  return (
    <Card className="p-6 mb-4 bg-gradient-to-br from-primary/5 to-primary/10">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">AI Tagging Progress</h3>
          <span className="text-2xl font-bold text-primary">
            {completionPercentage}%
          </span>
        </div>

        <Progress value={completionPercentage} className="h-3" />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-green-500/10">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">{completedFolders}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-500/10">
            <Clock className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-sm text-muted-foreground">In Progress</p>
              <p className="text-2xl font-bold">{inProgressFolders}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-orange-500/10">
            <AlertCircle className="h-8 w-8 text-orange-500" />
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold">{pendingFolders}</p>
            </div>
          </div>
        </div>

        <p className="text-sm text-muted-foreground text-center mt-2">
          {completedFolders} of {totalFolders} folders tagged
        </p>
      </div>
    </Card>
  );
};
