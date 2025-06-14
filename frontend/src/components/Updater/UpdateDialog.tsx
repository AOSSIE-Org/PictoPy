import React from 'react';
import { Update } from '@tauri-apps/plugin-updater';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertTriangle, Download, Clock, Calendar, Tag } from 'lucide-react';

interface UpdateDialogProps {
  update: Update;
  onDownload: () => void;
  onLater: () => void;
  isDownloading: boolean;
  downloadProgress: { downloaded: number; total: number };
  error?: string | null;
  open?: boolean;
}

const UpdateDialog: React.FC<UpdateDialogProps> = ({
  update,
  onDownload,
  onLater,
  isDownloading,
  downloadProgress,
  error,
  open = true,
}) => {
  const progressPercentage =
    downloadProgress.total > 0
      ? Math.round((downloadProgress.downloaded / downloadProgress.total) * 100)
      : 0;

  const formatBytes = (bytes: number) => {
    return Math.round((bytes / 1024 / 1024) * 100) / 100;
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Update Available
          </DialogTitle>
          <DialogDescription>
            A new version of the application is ready to install.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Version Information */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium">
                <Tag className="h-4 w-4" />
                Current Version:
              </span>
              <Badge variant="outline" className="font-mono">
                {update.currentVersion}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium">
                <Tag className="h-4 w-4" />
                New Version:
              </span>
              <Badge variant="default" className="font-mono">
                {update.version}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium">
                <Calendar className="h-4 w-4" />
                Release Date:
              </span>
              <span className="text-sm">
                {update.date
                  ? new Date(update.date).toLocaleDateString()
                  : 'N/A'}
              </span>
            </div>
          </div>

          <Separator />

          {/* Release Notes */}
          {update.body && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Release Notes:</h4>
              <ScrollArea className="h-32 w-full rounded-md border p-3">
                <pre className="text-xs whitespace-pre-wrap">{update.body}</pre>
              </ScrollArea>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Download Progress */}
          {isDownloading && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-medium">
                  <Download className="h-4 w-4 animate-bounce" />
                  Downloading update...
                </span>
                <Badge variant="secondary">{progressPercentage}%</Badge>
              </div>

              <Progress value={progressPercentage} className="w-full" />

              {downloadProgress.total > 0 && (
                <div className="text-muted-foreground text-center text-xs">
                  {formatBytes(downloadProgress.downloaded)} MB /{' '}
                  {formatBytes(downloadProgress.total)} MB
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
          <Button
            variant="outline"
            onClick={onLater}
            disabled={isDownloading}
            className="flex items-center gap-2"
          >
            <Clock className="h-4 w-4" />
            {error ? 'Close' : 'Later'}
          </Button>
          <Button
            onClick={onDownload}
            disabled={isDownloading || !!error}
            className="flex items-center gap-2"
          >
            {error ? (
              <>
                <AlertTriangle className="h-4 w-4" />
                Retry
              </>
            ) : isDownloading ? (
              <>
                <Download className="h-4 w-4" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Download & Install
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default UpdateDialog;
