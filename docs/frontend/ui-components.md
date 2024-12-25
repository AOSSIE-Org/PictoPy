# UI Components

## Core Components

### 1. Dialog

A modal dialog component based on Radix UI.

Key features:

- Customizable content, header, and footer
- Accessible design
- Animated transitions

Usage:

```jsx
<Dialog>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
    </DialogHeader>
    {/* Content */}
  </DialogContent>
</Dialog>
```

### 2. Input

A styled input component.

Usage:

```jsx
<Input type="text" placeholder="Enter text" />
```

### 3. Button

A versatile button component with various styles.

Usage:

```jsx
<Button variant="outline" onClick={handleClick}>
  Click me
</Button>
```

### 4. Dropdown Menu

A customizable dropdown menu component.

Usage:

```jsx
<DropdownMenu>
  <DropdownMenuTrigger>Open</DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem>Item 1</DropdownMenuItem>
    <DropdownMenuItem>Item 2</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

## Media Components

### 1. MediaCard

Displays an individual media item (image or video).

Usage:

```jsx
<MediaCard item={mediaItem} type="image" />
```

### 2. MediaGrid

Renders a grid of MediaCard components.

Usage:

```jsx
<MediaGrid
  mediaItems={items}
  itemsPerRow={3}
  openMediaViewer={handleOpen}
  type="image"
/>
```

### 3. MediaView

Provides a full-screen view of media items with navigation.

Usage:

```jsx
<MediaView
  initialIndex={0}
  onClose={handleClose}
  allMedia={mediaItems}
  currentPage={1}
  itemsPerPage={10}
  type="image"
/>
```

## Album Components

### 1. AlbumCard

Displays an individual album with cover image and actions.

Usage:

```jsx
<AlbumCard
  album={albumData}
  onClick={handleClick}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

### 2. AlbumList

Renders a grid of AlbumCard components.

Usage:

```jsx
<AlbumList
  albums={albumsData}
  albumsPerRow={3}
  onAlbumClick={handleAlbumClick}
  onEditAlbum={handleEdit}
  onDeleteAlbum={handleDelete}
/>
```

### 3. AlbumView

Displays the contents of a single album.

Usage:

```jsx
<AlbumView albumName="My Album" onBack={handleBack} onError={handleError} />
```

## Utility Components

### 1. LoadingScreen

Displays a full-screen loading indicator.

Usage:

```jsx
{
  isLoading && <LoadingScreen />;
}
```

### 2. ErrorDialog

Displays error messages in a dialog.

Usage:

```jsx
<ErrorDialog content={errorContent} onClose={handleClose} />
```

### 3. PaginationControls

Provides pagination controls for lists or grids.

Usage:

```jsx
<PaginationControls
  currentPage={1}
  totalPages={10}
  onPageChange={handlePageChange}
/>
```

## Form Components

### 1. CreateAlbumForm

A form dialog for creating new albums.

Usage:

```jsx
<CreateAlbumForm
  isOpen={isOpen}
  onClose={handleClose}
  onSuccess={handleSuccess}
  onError={handleError}
/>
```

### 2. EditAlbumDialog

A dialog for editing album details.

Usage:

```jsx
<EditAlbumDialog
  album={selectedAlbum}
  onClose={handleClose}
  onSuccess={handleSuccess}
  onError={handleError}
/>
```

## Best Practices

1. Use TypeScript for improved type safety.
2. Leverage Tailwind CSS for consistent styling.
3. Implement proper error handling and loading states.
4. Ensure accessibility in all components.
5. Optimize performance with React hooks like useMemo and useCallback.

## Customization

Most components accept a `className` prop for additional styling. Modify the base styles in component files or use a global CSS file for overrides.

For more detailed information on specific components, refer to the individual component files or consult the development team.
