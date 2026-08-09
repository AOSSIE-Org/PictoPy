import { Album } from './Album';

/** One address a share can be reached on. The backend lists these best first. */
export interface ShareUrl {
  interface: string;
  ip: string;
  url: string;
}

/** Mirrors the `Share` model in backend/app/schemas/share.py. */
export interface Share {
  token: string;
  album_id: string;
  album_name: string;
  image_count: number;
  port: number;
  created_at: string;
  expires_at: string | null;
  is_protected: boolean;
  urls: ShareUrl[];
}

/**
 * Where a share can be reached from. LAN keeps everything on the local network;
 * internet opens a tunnel, which means the photos pass through a third party.
 */
export type ShareMode = 'lan' | 'internet';

export interface CreateShareRequest {
  /** Omitted means the share lasts until it is revoked or PictoPy closes. */
  expires_in_minutes?: number;
  password?: string;
}

/** The view of the tunnel that `useShareTunnel` hands its caller. */
export interface ShareTunnel {
  /** The public address, or null when no tunnel is running. */
  url: string | null;
  isConnecting: boolean;
  /** Ask the owner what is running. Never throws. */
  refresh: () => Promise<string | null>;
  /** Open a tunnel to the share port. Rejects if no provider answers. */
  open: (port: number) => Promise<string>;
  /** Close any running tunnel. Rejects if it could not be closed. */
  close: () => Promise<void>;
}

export interface ShareAlbumDialogProps {
  album: Album | null;
  /**
   * Every live share for this album, newest first. An album can be shared more
   * than once, and stopping has to account for all of them.
   */
  shares: Share[];
  isOpen: boolean;
  onClose: () => void;
  /** Called after a share is created or revoked, so the list can refetch. */
  onChanged: () => void;
}
