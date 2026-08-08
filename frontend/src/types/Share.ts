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
