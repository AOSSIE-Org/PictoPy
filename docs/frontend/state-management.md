# State Management

This guide outlines the state management strategies used in our Tauri application, focusing on React hooks and component-level state management.

## Overview

Our application primarily uses React's built-in hooks for state management, including:

- `useState` for local component state
- `useMemo` for memoized values
- `useCallback` for memoized functions
- `Custom hooks` for shared logic and state

We also utilize props for passing data and functions between components.

## Key Concepts

### 1. Local Component State

We use `useState` for managing local component state. This is suitable for state that doesn't need to be shared across multiple components.

Example from `AlbumsView`:

```javascript
const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);
const [editingAlbum, setEditingAlbum] = (useState < Album) | (null > null);
const [currentAlbum, setCurrentAlbum] = (useState < string) | (null > null);
```

### 2. Memoization

We use `useMemo` for expensive computations or to prevent unnecessary re-renders.

Example from `MediaGallery`:

```javascript
const sortedMedia = useMemo(() => {
  return sortMedia(mediaItems, sortBy);
}, [mediaItems, sortBy]);

const currentItems = useMemo(() => {
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  return sortedMedia.slice(indexOfFirstItem, indexOfLastItem);
}, [sortedMedia, currentPage, itemsPerPage]);
```

### 3. Memoized Callbacks

`useCallback` is used to memoize functions, particularly event handlers. This helps to maintain referential equality between renders.

Example from `MediaGallery`:

```javascript
const handleSetSortBy = useCallback((value: string) => {
  setSortBy(value);
}, []);

const openMediaViewer = useCallback((index: number) => {
  setSelectedMediaIndex(index);
  setShowMediaViewer(true);
}, []);
```

### 4. Custom Hooks

We create custom hooks to encapsulate and share logic and state across components.

Examples:

- `useAllAlbums`
- `useDeleteAlbum`
- `useAIImage`
- `etc`

These hooks often manage their own state and provide functions to interact with that state.

### 5. Prop Drilling

We pass state and functions as props to child components. While this works for our current application structure, for deeper component trees, we might consider using Context API or a state management library.

Example from `AlbumsView`:

```javascript
<AlbumList
  albums={transformedAlbums}
  albumsPerRow={3}
  onAlbumClick={handleAlbumClick}
  onEditAlbum={(albumId) => {
    const album = albums.find((a) => a.album_name === albumId);
    if (album) {
      setEditingAlbum(album);
    }
  }}
  onDeleteAlbum={handleDeleteAlbum}
/>
```

## State Management Patterns

### 1. Lifting State Up

When state needs to be shared between sibling components, we lift it up to their closest common ancestor. This is seen in the `AlbumsView` component, which manages state for its child components.

### 2. Derived State

We use `useMemo` to create derived state based on props or other state values. This ensures that expensive calculations are only performed when necessary.

Example from `AIGallery`:

```javascript
const filteredMediaItems = useMemo(() => {
  return filterTag
    ? mediaItems.filter((mediaItem: any) => mediaItem.tags.includes(filterTag))
    : mediaItems;
}, [filterTag, mediaItems]);
```

### 3. State Initialization from Props

When initializing state based on props, we do it in the component body rather than inside useEffect to avoid unnecessary re-renders.

### 4. Error State Management

We manage error states at the component level and use a centralized error dialog to display errors.

Example from `AlbumsView`:

```javascript
const [errorDialogContent, setErrorDialogContent] = useState<{
  title: string;
  description: string;
} | null>(null);

const showErrorDialog = (title: string, err: unknown) => {
  setErrorDialogContent({
    title,
    description: err instanceof Error ? err.message : "An unknown error occurred",
  });
};
```

## Best Practices

1. Keep state as close to where it's used as possible.
2. Use `useMemo` and `useCallback` judiciously to optimize performance.
3. Create custom hooks to encapsulate complex state logic and side effects.
4. Use TypeScript to ensure type safety in state management.
5. Consider using Context API or a state management library if prop drilling becomes cumbersome.

By following these patterns and best practices, we maintain a clean and scalable state management system throughout our application.
