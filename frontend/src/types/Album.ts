export interface Album {
  album_name: string;
  image_paths: string[];
  description?: string;
  is_hidden?: boolean;
  password_protected?: boolean;
}

export interface AlbumFormData {
  name: string;
  description?: string;
  is_hidden?: boolean;
  password?: string;
}

export interface AlbumData {
  album_name: string;
  photos: string[];
  description?: string;
  folder_path: string;
  is_hidden?: boolean;
  password_protected?: boolean;
}

export interface CreateAlbumFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onError: (title: string, error: unknown) => void;
}

export interface EditAlbumDialogProps {
  album: Album | null;
  onClose: () => void;
  onSuccess: () => void;
  onError: (title: string, error: unknown) => void;
  requiresPassword?: boolean;
}

export interface ErrorDialogProps {
  content: { title: string; description: string } | null;
  onClose: () => void;
}

export interface AlbumListData {
  id: string;
  title: string;
  coverImage: string;
  imageCount: number;
  isHidden?: boolean;
  passwordProtected?: boolean;
}

export interface AlbumListProps {
  albums: AlbumListData[];
  albumsPerRow: number;
  onAlbumClick: (albumId: string) => void;
  onEditAlbum: (albumId: string) => void;
  onDeleteAlbum: (albumId: string) => void;
  showHiddenAlbums?: boolean;
}

export interface AlbumCardProps {
  album: AlbumListData;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onPasswordPrompt?: () => void;
}

export interface AlbumViewProps {
  albumName: string;
  onBack: () => void;
  onError: (title: string, error: unknown) => void;
  password?: string;
}

export interface PasswordPromptDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (password: string) => void;
  albumName: string;
}

export interface AddFolderResult {
  data: any | null;
  error: string | null;
  isLoading: boolean;
}

export interface AlbumActionResult {
  success: boolean;
  error?: string;
  data?: {
    album_name: string;
    is_hidden?: boolean;
    password_protected?: boolean;
  };
}

export interface AlbumOperation {
  type: 'create' | 'edit' | 'delete' | 'view';
  albumName: string;
  password?: string;
  data?: Partial<AlbumFormData>;
}

export interface AlbumCredentials {
  albumName: string;
  password?: string;
}

export type WithPassword<T> = T & {
  password?: string;
};
