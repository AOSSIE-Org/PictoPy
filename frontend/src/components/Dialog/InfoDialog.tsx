import { Info, AlertTriangle, CheckCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { InfoDialogProps } from '@/types/infoDialog';
import { useDispatch } from 'react-redux';
import { hideInfoDialog } from '@/features/infoDialogSlice';

export const InfoDialog: React.FC<InfoDialogProps> = ({
  isOpen,
  title,
  message,
  variant = 'info',
  showCloseButton = true,
}) => {
  const dispatch = useDispatch();

  const handleClose = () => {
    dispatch(hideInfoDialog());
  };

  // Define styles and icons based on variant
  const variantStyles = {
    info: {
      iconColor: 'text-primary',
      messageColor: '',
      icon: <Info className="h-5 w-5" />,
      buttonVariant: 'default' as const,
    },
    error: {
      iconColor: 'text-destructive',
      messageColor: 'text-destructive',
      icon: <AlertTriangle className="h-5 w-5" />,
      buttonVariant: 'destructive' as const,
    },
    success: {
      iconColor: 'text-green-500',
      messageColor: '',
      icon: <CheckCircle className="h-5 w-5" />,
      buttonVariant: 'default' as const,
    },
  };

  const { icon, iconColor, messageColor, buttonVariant } =
    variantStyles[variant];

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) handleClose();
      }}
    >
      <DialogContent className="sm:max-w-md" showCloseButton={showCloseButton}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className={iconColor}>{icon}</span>
            {title}
          </DialogTitle>
          <DialogDescription className={messageColor}>
            {message}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          {showCloseButton && (
            <Button
              className="cursor-pointer"
              variant={buttonVariant}
              onClick={handleClose}
            >
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
