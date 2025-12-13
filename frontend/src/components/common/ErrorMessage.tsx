/**
 * Error Message Component
 */

import React from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';

interface ErrorMessageProps {
  message: string;
  title?: string;
  onDismiss?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  title = 'Error',
  onDismiss 
}) => {
  return (
    <Alert variant="destructive" className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{message}</span>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 hover:opacity-70 transition-opacity"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </AlertDescription>
    </Alert>
  );
};

export default ErrorMessage;
