export type InfoDialogVariant = 'info' | 'error' | 'success';

export interface InfoDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  variant?: InfoDialogVariant;
  showCloseButton?: boolean;
}
