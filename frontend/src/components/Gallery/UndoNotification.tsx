import { Button } from '@/components/ui/button';
import { Undo2, X } from 'lucide-react';

interface UndoNotificationProps {
  message: string;
  onUndo: () => void;
  onDismiss: () => void;
}

export function UndoNotification({ message, onUndo, onDismiss }: UndoNotificationProps) {
  return (
    <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
      <div className="flex items-center gap-2">
        <span className="text-sm">{message}</span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onUndo}
          className="bg-white dark:bg-gray-800"
        >
          <Undo2 className="h-4 w-4 mr-2" />
          Undo
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}