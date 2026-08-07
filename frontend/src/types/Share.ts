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

export interface CreateShareRequest {
  /** Omitted means the share lasts until it is revoked or PictoPy closes. */
  expires_in_minutes?: number;
  password?: string;
}

export interface ShareAlbumDialogProps {
  album: Album | null;
  /** The album's existing share, if it is already being shared. */
  share: Share | null;
  isOpen: boolean;
  onClose: () => void;
  /** Called after a share is created or revoked, so the list can refetch. */
  onChanged: () => void;
}
