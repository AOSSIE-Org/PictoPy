export interface Album {
  id: string;
  name: string;
  description: string;
  is_locked: boolean;
  cover_image_path?: string;
  image_count: number;
  created_at: string;
  updated_at: string;
}

export interface AlbumFormData {
  name: string;
  description?: string;
  is_locked?: boolean;
  password?: string;
}

export interface CreateAlbumRequest {
  name: string;
  description?: string;
  is_locked?: boolean;
  password?: string;
}

export interface UpdateAlbumRequest {
  name?: string;
  description?: string;
  is_locked?: boolean;
  current_password?: string;
  password?: string;
}

export interface AddImagesToAlbumRequest {
  image_ids: string[];
}

export interface GetAlbumImagesRequest {
  password?: string;
}

export interface RemoveImagesFromAlbumRequest {
  image_ids: string[];
}

export interface EditAlbumDialogProps {
  album: Album | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export interface CreateAlbumDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export interface PasswordPromptDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (password: string) => void;
  albumName: string;
}

export interface AddImagesToAlbumDialogProps {
  isOpen: boolean;
  onClose: () => void;
  albumId: string;
  albumName: string;
}

export interface AlbumCardProps {
  album: Album;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
}
