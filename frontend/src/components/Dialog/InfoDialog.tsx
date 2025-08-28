import React from 'react';
import { Info } from 'lucide-react';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { InfoDialogProps } from '@/types/infoDialog';
import { useDispatch } from 'react-redux';
import { hideInfoDialog } from '@/features/infoDialogSlice';

export const InfoDialog: React.FC<InfoDialogProps> = ({
  isOpen,
  title,
  message
}) => {
  const dispatch = useDispatch();

  const handleClose = () => {
    dispatch(hideInfoDialog());
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => {
      if (!open) handleClose();
    }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-primary" />
            {title}
          </DialogTitle>
          <DialogDescription>
            {message}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={handleClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
