export interface Album {
  name: string;
  image_paths: string[];
  description?: string;
}
export interface AddFolderResult {
  data: any | null;
  error: string | null;
  isLoading: boolean;
}

export interface Album {
  album_name: string;
  image_paths: string[];
  description?: string;
}

export interface Album {
  album_name: string;
  image_paths: string[];
  description?: string;
}

export interface AlbumData {
  album_name: string;
  photos: string[];
  description?: string;
  folder_path: string;
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
}

export interface AlbumListProps {
  albums: AlbumListData[];
  albumsPerRow: number;
  onAlbumClick: (albumId: string) => void;
  onEditAlbum: (albumId: string) => void;
  onDeleteAlbum: (albumId: string) => void;
}
export interface AlbumCardProps {
  album: AlbumListData;
  onClick: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export interface AlbumViewProps {
  albumName: string;
  onBack: () => void;
  onError: (title: string, error: unknown) => void;
}
