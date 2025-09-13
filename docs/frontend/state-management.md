# State Management with Redux

This guide outlines the Redux-based state management system used in our PictoPy application, focusing on Redux slices and store configuration.

## Overview

Our application uses Redux Toolkit for state management, which provides:

- **Redux slices** for feature-based state organization
- **Async thunks** for handling asynchronous operations
- **Immutable state updates** with Immer
- **TypeScript integration** for type safety

The Redux store serves as the single source of truth for application state that needs to be shared across multiple components.

## Store Structure

Our Redux store is organized into the following slices:

### 1. Media Slice

Manages the state for photos, videos, and media-related operations.

**State Structure:**
```typescript
interface MediaState {
  photos: Photo[];
  videos: Video[];
  currentMedia: Media | null;
  loading: boolean;
  error: string | null;
  filters: {
    dateRange: DateRange;
    tags: string[];
    sortBy: 'date' | 'name' | 'size';
  };
}
```

**Key Actions:**
- `setPhotos` - Updates the photos array
- `setVideos` - Updates the videos array  
- `setCurrentMedia` - Sets the currently selected media item
- `updateFilters` - Updates media filtering options
- `clearError` - Clears error states

### 2. UI Slice

Manages global UI state and user interface preferences.

**State Structure:**
```typescript
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  viewMode: 'grid' | 'list';
  selectedItems: string[];
  showPreview: boolean;
  notifications: Notification[];
}
```

**Key Actions:**
- `toggleSidebar` - Opens/closes the sidebar
- `setTheme` - Changes the application theme
- `setViewMode` - Switches between grid and list view
- `selectItems` - Manages selected media items
- `addNotification` - Adds system notifications

### 3. Albums Slice

Handles album creation, editing, and management.

**State Structure:**
```typescript
interface AlbumsState {
  albums: Album[];
  currentAlbum: Album | null;
  loading: boolean;
  error: string | null;
}
```

**Key Actions:**
- `setAlbums` - Updates the albums list
- `addAlbum` - Creates a new album
- `updateAlbum` - Modifies an existing album
- `deleteAlbum` - Removes an album
- `setCurrentAlbum` - Sets the active album

### 4. Settings Slice

Manages user preferences and application settings.

**State Structure:**
```typescript
interface SettingsState {
  directories: string[];
  autoBackup: boolean;
  compressionLevel: number;
  thumbnailSize: 'small' | 'medium' | 'large';
  secureFolder: {
    enabled: boolean;
    path: string;
  };
}
```

**Key Actions:**
- `updateDirectories` - Modifies watched directories
- `toggleAutoBackup` - Enables/disables auto backup
- `setCompressionLevel` - Adjusts image compression
- `setThumbnailSize` - Changes thumbnail display size

## Redux Toolkit Configuration

### Store Setup

```typescript
import { configureStore } from '@reduxjs/toolkit';
import mediaReducer from './slices/mediaSlice';
import uiReducer from './slices/uiSlice';
import albumsReducer from './slices/albumsSlice';
import settingsReducer from './slices/settingsSlice';

export const store = configureStore({
  reducer: {
    media: mediaReducer,
    ui: uiReducer,
    albums: albumsReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Async Thunks

We use createAsyncThunk for handling asynchronous operations:

```typescript
export const loadPhotos = createAsyncThunk(
  'media/loadPhotos',
  async (directories: string[], { rejectWithValue }) => {
    try {
      const photos = await invoke('get_server_path');
      return photos;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const createAlbum = createAsyncThunk(
  'albums/create',
  async (albumData: NewAlbum, { rejectWithValue }) => {
    try {
      const album = await invoke('create_album', albumData);
      return album;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);
```

## Usage in Components

### Connecting Components

Use the `useSelector` and `useDispatch` hooks to connect components to the Redux store:

```typescript
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import { setPhotos, updateFilters } from '../store/slices/mediaSlice';

const MediaGallery = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { photos, loading, filters } = useSelector((state: RootState) => state.media);
  const { viewMode } = useSelector((state: RootState) => state.ui);

  const handleFilterChange = (newFilters: FilterOptions) => {
    dispatch(updateFilters(newFilters));
  };

  // Component logic...
};
```

### Typed Hooks

For better TypeScript support, we use typed versions of the hooks:

```typescript
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

## Best Practices

1. **Keep slices focused** - Each slice should manage a specific domain of your application
2. **Use createAsyncThunk** - For all async operations that need to update the store
3. **Normalize state shape** - Use normalized data structures for complex relational data
4. **Use RTK Query** - For advanced data fetching and caching needs
5. **Implement error handling** - Always handle loading and error states in async thunks
6. **Use selectors** - Create reusable selectors for complex state derivations

## State Persistence

We use Redux Persist to maintain state across app restarts:

```typescript
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['settings', 'albums'], // Only persist settings and albums
};

const persistedReducer = persistReducer(persistConfig, rootReducer);
```

This Redux-based architecture provides a scalable and maintainable state management solution that grows with our application's complexity.