import React, { useState } from 'react';
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
import { PasswordPromptDialogProps } from '@/types/Album';
import { Lock, Eye, EyeOff } from 'lucide-react';

export const AlbumPasswordDialog: React.FC<PasswordPromptDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  albumName,
}) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError('Password is required');
      return;
    }
    onSubmit(password);
    handleClose();
  };

  const handleClose = () => {
    setPassword('');
    setError('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[400px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <div className="bg-primary/10 mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full">
              <Lock className="text-primary h-6 w-6" />
            </div>
            <DialogTitle className="text-center">
              This Album is Protected
            </DialogTitle>
            <DialogDescription className="text-center">
              Enter the password to access "{albumName}"
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="password">Password *</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter password"
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
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit">Unlock Album</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
