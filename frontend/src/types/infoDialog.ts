import { ReactNode } from 'react';

export type InfoDialogVariant = 'info' | 'error' | 'warning';

export interface InfoDialogAction {
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}

export interface InfoDialogProps {
  isOpen: boolean;
  title: string;
  message: string | ReactNode;
  variant?: InfoDialogVariant;
  showCloseButton?: boolean;
  primaryAction?: InfoDialogAction;
}
