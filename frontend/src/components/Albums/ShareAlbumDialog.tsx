import React, { useEffect, useState, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { QRCodeSVG } from 'qrcode.react';
import { openUrl } from '@tauri-apps/plugin-opener';
import {
  Check,
  Copy,
  Globe,
  Info,
  Loader2,
  Share2,
  TriangleAlert,
  Wifi,
} from 'lucide-react';
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
import { Separator } from '@/components/ui/separator';
import { usePictoMutation, type BackendRes } from '@/hooks/useQueryExtension';
import { createShare, revokeShare } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { cn } from '@/lib/utils';
import { useShareTunnel } from '@/hooks/useShareTunnel';
import {
  Share,
  ShareAlbumDialogProps,
  ShareMode,
  ShareUrl,
} from '@/types/Share';

const MODE_OPTIONS = [
  { value: 'lan', label: 'This network', icon: Wifi },
  { value: 'internet', label: 'Internet', icon: Globe },
] as const satisfies ReadonlyArray<{
  value: ShareMode;
  label: string;
  icon: typeof Wifi;
}>;

const EXPIRY_OPTIONS = [
  { value: '60', label: 'For 1 hour' },
  { value: '360', label: 'For 6 hours' },
  { value: '1440', label: 'For 24 hours' },
  { value: 'never', label: 'Until I stop it' },
] as const;

// The backend hashes with bcrypt and refuses anything shorter.
const MIN_PASSWORD_LENGTH = 4;

const DOCS_URL =
  'https://aossie-org.github.io/PictoPy/overview/sharing-albums/';
const DOCS_INTERNET_URL = `${DOCS_URL}#internet-mode`;

const formatExpiry = (expiresAt: string | null): string =>
  expiresAt ? new Date(expiresAt).toLocaleString() : 'Until you stop it';

export const ShareAlbumDialog: React.FC<ShareAlbumDialogProps> = ({
  album,
  shares,
  isOpen,
  onClose,
  onChanged,
}) => {
  const userInteracted = useRef(false);
  const dispatch = useDispatch();
  const [mode, setMode] = useState<ShareMode>('lan');
  const [expiry, setExpiry] = useState<string>('1440');
  const [withPassword, setWithPassword] = useState(false);
  const [password, setPassword] = useState('');
  // Kept apart from the password field's own validation message so a failed
  // connection does not put a red border round an unrelated input.
  const [error, setError] = useState('');
  const [tunnelError, setTunnelError] = useState('');
  const [createdShare, setCreatedShare] = useState<Share | null>(null);
  const [selectedUrl, setSelectedUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const tunnel = useShareTunnel();
  const { url: tunnelUrl, isConnecting } = tunnel;

  // The share this dialog is showing: the one just made, or the newest already
  // running. Older ones stay out of the way until sharing is stopped.
  const activeShare = createdShare ?? shares[0] ?? null;

  // A tunnel forwards the whole share port, so its address reaches the same
  // album as the LAN ones. Showing it alone keeps the link the user asked for
  // from competing with addresses that only work inside the house.
  const urls: ShareUrl[] = tunnelUrl
    ? [
        {
          interface: 'Internet',
          ip: new URL(tunnelUrl).hostname,
          url: `${tunnelUrl}/s/${activeShare?.token ?? ''}`,
        },
      ]
    : (activeShare?.urls ?? []);
  const shareUrl = urls.find((entry) => entry.url === selectedUrl) ?? urls[0];

  // Every token that would still serve this album. Creating leaves earlier
  // shares valid, so stopping has to take them all down together.
  const activeTokens = Array.from(
    new Set([
      ...(createdShare ? [createdShare.token] : []),
      ...shares.map((entry) => entry.token),
    ]),
  );

  const createShareMutation = usePictoMutation({
    mutationFn: (variables: { albumId: string; password?: string }) =>
      createShare(variables.albumId, {
        ...(expiry !== 'never' && { expires_in_minutes: Number(expiry) }),
        ...(variables.password && { password: variables.password }),
      }),
    // Handled here rather than through the feedback hook so the new share
    // arrives typed rather than as the hook's untyped success payload.
    onSuccess: async (response) => {
      const share = response.data;
      if (!share) {
        return;
      }
      if (mode === 'lan') {
        setCreatedShare(share);
        onChanged();
        return;
      }

      try {
        await tunnel.open(share.port);
        setCreatedShare(share);
      } catch (cause) {
        // The user asked for an internet share and did not get one, so undo
        // the local half rather than leaving a share they did not ask for.
        try {
          await revokeShare(share.token);
          setTunnelError(
            `Could not open a connection: ${String(cause)} The album was not shared.`,
          );
        } catch {
          // Saying "not shared" here would be untrue, and the share is live on
          // the local network with nothing telling the user so.
          setTunnelError(
            `Could not open a connection: ${String(cause)} The album is still being shared on this network. Reopen this dialog to stop it.`,
          );
        }
      } finally {
        onChanged();
      }
    },
    autoInvalidateTags: ['shares'],
  });

  const revokeShareMutation = usePictoMutation({
    // Takes every token rather than one, so "stop sharing" leaves nothing
    // serving the album. Wrapped rather than passed straight through because
    // react-query hands the mutation function a context as a second argument.
    mutationFn: async (tokens: string[]): Promise<BackendRes<null>> => {
      await Promise.all(tokens.map((token) => revokeShare(token)));
      // Closed through the hook, which asks whether one is running rather than
      // reading state this dialog may not have received yet. A failure here
      // rejects the mutation, so nothing claims the cleanup finished.
      await tunnel.close();
      return { success: true };
    },
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
    successMessage: 'The album is no longer being shared.',
    errorTitle: 'Error',
    errorMessage:
      'The share may still be running. Reopen this dialog and try stopping it again.',
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
    
    userInteracted.current = false; // Reset interaction flag on open
    
    setMode('lan');
    setExpiry('1440');
    setWithPassword(false);
    setPassword('');
    setError('');
    setTunnelError('');
    setCreatedShare(null);
    setSelectedUrl('');
    setCopied(false);
    
    // A share made earlier is still served by whatever tunnel is up, so ask
    // rather than assume it was a local one. The mode follows the answer:
    // showing an internet link while the help button explains local sharing
    // would describe the wrong thing.
    tunnel.refresh().then((current) => {
      if (current && !userInteracted.current) { // Prevent overriding user's manual selection
        setMode('internet');
        // Same safer default the manual switch applies: an internet link is
        // public, so it starts protected however the mode was arrived at.
        setWithPassword(true);
      }
    });
  }, [isOpen, album?.id, tunnel.refresh]);

  const handleModeChange = (next: ShareMode) => {
    userInteracted.current = true; // Mark that user took control
    setMode(next);
    setError('');
    setTunnelError('');
    // Anyone with the link can open it, and messaging apps fetch links to build
    // previews. Starting protected is the safer default; it stays removable.
    setWithPassword(next === 'internet');
  };

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

  // Deep links to the section covering whichever mode is selected, so someone
  // weighing up internet mode lands on what it costs rather than the top.
  const docsButton = (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="text-muted-foreground hover:text-foreground h-7 w-7 shrink-0"
      aria-label="How sharing works"
      onClick={() => {
        const url = mode === 'internet' ? DOCS_INTERNET_URL : DOCS_URL;
        // Hand the address over rather than failing quietly: if the browser
        // cannot be launched there is nothing else to tell the user what
        // happened, and the page is still readable by other means.
        openUrl(url).catch(() =>
          dispatch(
            showInfoDialog({
              title: 'Could not open your browser',
              message: `Open this page instead: ${url}`,
              variant: 'error',
            }),
          ),
        );
      }}
    >
      <Info className="h-4 w-4" />
    </Button>
  );

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
      <DialogContent
        className={cn(
          // Nothing caps a dialog's height by default, so a tall one runs off
          // the screen with its buttons out of reach.
          'max-h-[90vh] overflow-y-auto',
          activeShare ? 'sm:max-w-3xl' : 'sm:max-w-[480px]',
        )}
      >
        {isConnecting ? (
          <>
            <DialogHeader>
              <DialogTitle>Starting a secure connection</DialogTitle>
              <DialogDescription>
                Opening a route to this machine so the album can be reached from
                outside your network.
              </DialogDescription>
            </DialogHeader>
            <div
              className="flex flex-col items-center justify-center gap-3 py-10"
              role="status"
            >
              <Loader2 className="text-primary h-8 w-8 animate-spin" />
              <p className="text-muted-foreground text-sm">
                This usually takes a few seconds.
              </p>
            </div>
          </>
        ) : activeShare ? (
          <>
            <DialogHeader>
              <div className="flex items-center gap-1">
                <DialogTitle className="truncate">
                  Sharing "{activeShare.album_name}"
                </DialogTitle>
                {docsButton}
              </div>
              <DialogDescription>
                {tunnelUrl
                  ? 'Anyone with this link can open the album while PictoPy is running. It travels through a relay that can see the photos.'
                  : 'Anyone on this network can open the link while PictoPy is running. Nothing is uploaded.'}
              </DialogDescription>
            </DialogHeader>

            {/* Two columns rather than one card taller than the window: what
                you hand to someone on the left, what you manage on the right. */}
            <div className="grid gap-6 py-2 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
              <div className="flex flex-col gap-4">
                {shareUrl ? (
                  <>
                    <div className="flex justify-center">
                      {/* Always on white: a QR code needs the light quiet zone
                          to stay scannable in dark mode. */}
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
                    <span className="font-medium">
                      {activeShare.image_count}
                    </span>
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

              <Separator orientation="vertical" className="hidden md:block" />

              <div className="flex min-w-0 flex-col gap-4">
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
                    {/* Scrolls on its own: a machine with a stack of virtual
                        adapters can list a lot of these. Capped rather than
                        fixed so two addresses do not sit in an empty box. */}
                    <div className="grid max-h-62 gap-1.5 overflow-y-auto pr-1">
                      {urls.map(renderAddress)}
                    </div>
                  </div>
                )}

                {/* Pushed down so the buttons line up with the bottom of the
                    QR column instead of floating mid-panel. */}
                <div className="mt-auto flex gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="text-destructive flex-1"
                    onClick={() => revokeShareMutation.mutate(activeTokens)}
                    disabled={revokeShareMutation.isPending}
                  >
                    Stop sharing
                  </Button>
                  <Button type="button" className="flex-1" onClick={onClose}>
                    Done
                  </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <div className="flex items-center gap-1">
                <DialogTitle className="truncate">
                  Share "{album?.name}"
                </DialogTitle>
                {docsButton}
              </div>
              <DialogDescription>
                {mode === 'lan'
                  ? 'Serve this album to other devices on your network. The photos stay on this machine.'
                  : 'Serve this album to anyone with the link, wherever they are.'}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              {/* Full width, because this is the decision the rest of the form
                  hangs off rather than one setting among several. */}
              <div className="bg-muted grid w-full grid-cols-2 gap-1 rounded-lg p-1">
                {MODE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-checked={mode === option.value}
                    onClick={() => handleModeChange(option.value)}
                    className={cn(
                      'flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      mode === option.value
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    <option.icon className="h-4 w-4" />
                    {option.label}
                  </button>
                ))}
              </div>

              {mode === 'internet' && (
                <div className="border-destructive/40 bg-destructive/5 grid gap-1.5 rounded-md border p-3">
                  <p className="flex items-center gap-2 text-sm font-medium">
                    <TriangleAlert className="text-destructive h-4 w-4 shrink-0" />
                    The link leaves your network
                  </p>
                  <p className="text-muted-foreground text-xs">
                    Photos pass through a tunnel service, which can see them.
                    Anyone holding the link can open the album, and chat apps
                    such as WhatsApp and Slack fetch links automatically to
                    build previews, a password stops those previews seeing
                    anything.
                  </p>
                </div>
              )}

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
                    userInteracted.current = true; // Mark that user took control
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

            {tunnelError && (
              <p className="text-destructive pb-2 text-sm" role="alert">
                {tunnelError}
              </p>
            )}

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