import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/app/store';
import { hideInfoDialog } from '@/features/infoDialogSlice';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

const GlobalInfoDialog: React.FC = () => {
  const dispatch = useDispatch();
  const { open, title, description, variant } = useSelector(
    (state: RootState) => state.infoDialog,
  );

  const handleClose = () => {
    dispatch(hideInfoDialog());
  };

  const getIcon = () => {
    switch (variant) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'destructive':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getAlertVariant = () => {
    switch (variant) {
      case 'destructive':
        return 'destructive';
      default:
        return 'default';
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getIcon()}
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Alert variant={getAlertVariant()}>
            {getIcon()}
            <AlertDescription>{description}</AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button onClick={handleClose} className="w-full">
            OK
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default GlobalInfoDialog;
