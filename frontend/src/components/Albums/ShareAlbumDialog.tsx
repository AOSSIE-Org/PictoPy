import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Check, Copy, Share2, Wifi } from 'lucide-react';
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
import { Switch } from '@/components/ui/switch';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { createShare, revokeShare } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { cn } from '@/lib/utils';
import { Share, ShareAlbumDialogProps, ShareUrl } from '@/types/Share';

const EXPIRY_OPTIONS = [
  { value: '60', label: 'For 1 hour' },
  { value: '360', label: 'For 6 hours' },
  { value: '1440', label: 'For 24 hours' },
  { value: 'never', label: 'Until I stop it' },
] as const;

// The backend hashes with bcrypt and refuses anything shorter.
const MIN_PASSWORD_LENGTH = 4;

const formatExpiry = (expiresAt: string | null): string =>
  expiresAt ? new Date(expiresAt).toLocaleString() : 'Until you stop it';

export const ShareAlbumDialog: React.FC<ShareAlbumDialogProps> = ({
  album,
  share,
  isOpen,
  onClose,
  onChanged,
}) => {
  const [expiry, setExpiry] = useState<string>('1440');
  const [withPassword, setWithPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [createdShare, setCreatedShare] = useState<Share | null>(null);
  const [selectedUrl, setSelectedUrl] = useState('');
  const [copied, setCopied] = useState(false);

  // The share this dialog is showing: the one just made, or one already running.
  const activeShare = createdShare ?? share;
  const urls = activeShare?.urls ?? [];
  const shareUrl = urls.find((entry) => entry.url === selectedUrl) ?? urls[0];

  const createShareMutation = usePictoMutation({
    mutationFn: (variables: { albumId: string; password?: string }) =>
      createShare(variables.albumId, {
        ...(expiry !== 'never' && { expires_in_minutes: Number(expiry) }),
        ...(variables.password && { password: variables.password }),
      }),
    // Handled here rather than through the feedback hook so the new share
    // arrives typed rather than as the hook's untyped success payload.
    onSuccess: (response) => {
      if (response.data) {
        setCreatedShare(response.data);
      }
      onChanged();
    },
    autoInvalidateTags: ['shares'],
  });

  const revokeShareMutation = usePictoMutation({
    // Wrapped rather than passed directly: react-query hands the mutation
    // function a context object as a second argument.
    mutationFn: (token: string) => revokeShare(token),
    autoInvalidateTags: ['shares'],
  });

  useMutationFeedback(createShareMutation, {
    loadingMessage: 'Starting the share...',
    // The link and QR code are the confirmation; a dialog on top of them would
    // only be in the way.
    showSuccess: false,
    errorTitle: 'Error',
    errorMessage: 'Could not share this album. Please try again.',
  });

  useMutationFeedback(revokeShareMutation, {
    loadingMessage: 'Stopping the share...',
    successTitle: 'Sharing stopped',
    successMessage: 'The album is no longer on the local network.',
    errorTitle: 'Error',
    errorMessage: 'Could not stop this share. Please try again.',
    onSuccess: () => {
      onChanged();
      onClose();
    },
  });

  // Reopening has to start clean, including after sharing a different album.
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setExpiry('1440');
    setWithPassword(false);
    setPassword('');
    setError('');
    setCreatedShare(null);
    setSelectedUrl('');
    setCopied(false);
  }, [isOpen, album?.id]);

  const handleCreate = (event: React.FormEvent) => {
    event.preventDefault();
    if (!album) {
      return;
    }
    if (withPassword && password.trim().length < MIN_PASSWORD_LENGTH) {
      setError(`Use at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    createShareMutation.mutate({
      albumId: album.id,
      ...(withPassword && { password: password.trim() }),
    });
  };

  const handleCopy = async () => {
    if (!shareUrl || !navigator.clipboard) {
      return;
    }
    await navigator.clipboard.writeText(shareUrl.url);
    setCopied(true);
  };

  const renderAddress = (entry: ShareUrl) => (
    <button
      key={entry.url}
      type="button"
      onClick={() => {
        setSelectedUrl(entry.url);
        setCopied(false);
      }}
      className={cn(
        'flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm',
        entry.url === shareUrl?.url
          ? 'border-primary bg-primary/5'
          : 'border-border hover:bg-muted',
      )}
    >
      <span className="truncate font-medium">{entry.interface}</span>
      <span className="text-muted-foreground ml-3 shrink-0 font-mono text-xs">
        {entry.ip}
      </span>
    </button>
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[480px]">
        {activeShare ? (
          <>
            <DialogHeader>
              <DialogTitle>Sharing "{activeShare.album_name}"</DialogTitle>
              <DialogDescription>
                Anyone on this network can open the link while PictoPy is
                running. Nothing is uploaded.
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              {shareUrl ? (
                <>
                  <div className="flex justify-center">
                    {/* Always on white: a QR code needs the light quiet zone to
                        stay scannable in dark mode. */}
                    <div className="rounded-xl bg-white p-3 shadow-sm">
                      <QRCodeSVG value={shareUrl.url} size={168} />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="share-link">Link</Label>
                    <div className="flex gap-2">
                      <Input
                        id="share-link"
                        readOnly
                        value={shareUrl.url}
                        className="font-mono text-xs"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={handleCopy}
                        aria-label="Copy link"
                      >
                        {copied ? (
                          <Check className="h-4 w-4" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {urls.length > 1 && (
                    <div className="grid gap-2">
                      <Label className="flex items-center gap-2">
                        <Wifi className="text-primary h-4 w-4" />
                        Address
                      </Label>
                      <p className="text-muted-foreground text-xs">
                        This machine has more than one. If the first does not
                        work, try another.
                      </p>
                      <div className="grid gap-1.5">
                        {urls.map(renderAddress)}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground text-sm">
                  No local network address was found, so the album cannot be
                  reached from another device. Connect to a network and share
                  again.
                </p>
              )}

              <div className="bg-muted grid gap-1 rounded-md p-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Photos</span>
                  <span className="font-medium">{activeShare.image_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Expires</span>
                  <span className="font-medium">
                    {formatExpiry(activeShare.expires_at)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Password</span>
                  <span className="font-medium">
                    {activeShare.is_protected ? 'Required' : 'None'}
                  </span>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                className="text-destructive"
                onClick={() => revokeShareMutation.mutate(activeShare.token)}
                disabled={revokeShareMutation.isPending}
              >
                Stop sharing
              </Button>
              <Button type="button" onClick={onClose}>
                Done
              </Button>
            </DialogFooter>
          </>
        ) : (
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Share "{album?.name}"</DialogTitle>
              <DialogDescription>
                Serve this album to other devices on your network. The photos
                stay on this machine.
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label>Keep sharing</Label>
                <RadioGroup value={expiry} onValueChange={setExpiry}>
                  {EXPIRY_OPTIONS.map((option) => (
                    <div key={option.value} className="flex items-center gap-2">
                      <RadioGroupItem
                        value={option.value}
                        id={`expiry-${option.value}`}
                      />
                      <Label
                        htmlFor={`expiry-${option.value}`}
                        className="font-normal"
                      >
                        {option.label}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
                <p className="text-muted-foreground text-xs">
                  Sharing always stops when PictoPy closes.
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="share-password-toggle">
                    Require a password
                  </Label>
                  <p className="text-muted-foreground text-sm">
                    Asked for before any photo loads
                  </p>
                </div>
                <Switch
                  id="share-password-toggle"
                  checked={withPassword}
                  onCheckedChange={(checked) => {
                    setWithPassword(checked);
                    setError('');
                  }}
                />
              </div>

              {withPassword && (
                <div className="grid gap-2">
                  <Label htmlFor="share-password">Password</Label>
                  <Input
                    id="share-password"
                    type="password"
                    placeholder="Enter a password"
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      setError('');
                    }}
                    className={error ? 'border-destructive' : ''}
                  />
                  {error && <p className="text-destructive text-sm">{error}</p>}
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={createShareMutation.isPending}>
                <Share2 className="mr-2 h-4 w-4" />
                Start sharing
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
};
