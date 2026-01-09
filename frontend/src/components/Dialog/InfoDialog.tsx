import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';
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

interface ExtendedInfoDialogProps extends InfoDialogProps {
  onClose?: () => void;
}

export const InfoDialog: React.FC<ExtendedInfoDialogProps> = ({
  isOpen,
  title,
  message,
  variant = 'info',
  showCloseButton = true,
  primaryAction,
  onClose,
}) => {
  const dispatch = useDispatch();

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      dispatch(hideInfoDialog());
    }
  };

  // Define styles and icons based on variant
  const variantStyles = {
    info: {
      iconColor: 'text-primary',
      messageColor: '',
      icon: <Info className="h-5 w-5" />,
      buttonVariant: 'default' as const,
    },
    warning: {
      iconColor: 'text-yellow-500',
      messageColor: '',
      icon: <AlertTriangle className="h-5 w-5" />,
      buttonVariant: 'default' as const,
    },
    error: {
      iconColor: 'text-destructive',
      messageColor: 'text-destructive',
      icon: <AlertTriangle className="h-5 w-5" />,
      buttonVariant: 'destructive' as const,
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
          <DialogDescription
            className={messageColor}
            asChild={typeof message !== 'string'}
          >
            {typeof message === 'string' ? message : <div>{message}</div>}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex-row justify-end gap-2 sm:gap-2">
          {primaryAction && (
            <Button
              className="cursor-pointer"
              variant="default"
              onClick={primaryAction.onClick}
              disabled={primaryAction.disabled}
            >
              {primaryAction.icon && (
                <span className="mr-2">{primaryAction.icon}</span>
              )}
              {primaryAction.label}
            </Button>
          )}
          {showCloseButton && (
            <Button
              className="cursor-pointer"
              variant={primaryAction ? 'outline' : buttonVariant}
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
