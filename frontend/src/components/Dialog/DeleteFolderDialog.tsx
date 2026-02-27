import { FC } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface DeleteFolderDialogProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  onConfirm: () => void;
  folderPath: string;
}

const DeleteFolderDialog: FC<DeleteFolderDialogProps> = ({
  isOpen,
  setIsOpen,
  onConfirm,
  folderPath,
}) => {
  const handleConfirm = () => {
    onConfirm();
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <DialogTitle className="text-xl">Delete Folder?</DialogTitle>
          </div>
          <DialogDescription className="pt-4 text-left">
            <div className="space-y-3">
              <p className="font-medium text-foreground">
                You are about to remove this folder from your library:
              </p>
              <div className="rounded-md bg-muted p-3">
                <code className="text-sm break-all">{folderPath}</code>
              </div>
              <div className="space-y-2 text-sm">
                <p className="font-semibold text-yellow-700 dark:text-yellow-400">
                  ⚠️ This action will:
                </p>
                <ul className="ml-4 space-y-1 list-disc text-muted-foreground">
                  <li>Remove the folder from your PictoPy library</li>
                  <li>Delete all photos in this folder from the library</li>
                  <li>Remove all face recognition data for these photos</li>
                  <li>Delete all AI-generated tags and clusters</li>
                </ul>
              </div>
              <div className="rounded-md border border-green-300 bg-green-50 p-3 dark:border-green-700 dark:bg-green-900/20">
                <p className="text-sm font-medium text-green-800 dark:text-green-300">
                  ✓ Your actual files on disk will NOT be deleted
                </p>
              </div>
            </div>
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => setIsOpen(false)}
            className="cursor-pointer"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            className="cursor-pointer"
          >
            Delete from Library
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DeleteFolderDialog;
