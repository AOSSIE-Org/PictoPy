import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertTriangle, Eye, EyeOff } from 'lucide-react';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (password?: string) => void;
  albumName: string;
  isLocked?: boolean;
}

export const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  albumName,
  isLocked = false,
}) => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  // Reset internal input state when dialog visibility changes
  useEffect(() => {
    if (!isOpen) {
      setPassword('');
      setError('');
      setShowPassword(false);
    }
  }, [isOpen]);

  const handleConfirm = () => {
    // If the album is locked, password is required before proceeding with deletion
    if (isLocked) {
      if (!password.trim()) {
        setError('Password is required to delete a locked album');
        return;
      }
      onConfirm(password);
    } else {
      onConfirm();
    }
  };

  const handleClose = () => {
    setPassword('');
    setError('');
    setShowPassword(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="bg-destructive/10 mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full">
            <AlertTriangle className="text-destructive h-6 w-6" />
          </div>
          <DialogTitle className="text-center">Delete Album</DialogTitle>
          <DialogDescription className="text-center">
            Are you sure you want to delete "{albumName}"? This action cannot be
            undone.
          </DialogDescription>
        </DialogHeader>

        {isLocked && (
          <div className="grid gap-2 py-2">
            <Label htmlFor="delete-album-password">Album Password *</Label>
            <div className="relative">
              <Input
                id="delete-album-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter password to confirm"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError('');
                }}
                className={error ? 'border-destructive' : ''}
                autoFocus
              />
              <button
                type="button"
                className="absolute top-0 right-0 mr-2 flex h-full items-center"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-gray-400" />
                ) : (
                  <Eye className="h-4 w-4 text-gray-400" />
                )}
              </button>
            </div>
            {error && <p className="text-destructive text-sm">{error}</p>}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={handleConfirm}>
            Delete Album
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
