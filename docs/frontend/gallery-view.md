# Gallery View

The Gallery View is a core feature of our Tauri application, providing users with an intuitive interface to browse, sort, and interact with their media items (images and videos).

## Components Overview

1. MediaGallery
2. MediaGrid
3. MediaCard
4. MediaView
5. SortingControls
6. PaginationControls

## MediaGallery

The main container component for the gallery view.

### Key Features

- Manages sorting and pagination state
- Renders the grid of media items
- Handles opening and closing of full-screen media view

### Usage

```jsx
import MediaGallery from "./MediaGallery";

<MediaGallery mediaItems={items} title="My Gallery" type="image" />;
```

### Implementation Details

```jsx
export default function MediaGallery({
  mediaItems,
  title,
  type,
}: MediaGalleryProps) {
  const [sortBy, setSortBy] = useState<string>("date");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showMediaViewer, setShowMediaViewer] = useState<boolean>(false);
  const [selectedMediaIndex, setSelectedMediaIndex] = useState<number>(0);

  // Memoized sorted and paginated media items
  const sortedMedia = useMemo(() => sortMedia(mediaItems, sortBy), [mediaItems, sortBy]);
  const currentItems = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    return sortedMedia.slice(indexOfFirstItem, indexOfLastItem);
  }, [sortedMedia, currentPage]);

  // ... other memoized values and callback functions

  return (
    <div className="container">
      <div className="dark:bg-background dark:text-foreground max-w-6xl mx-auto px-4 md:px-6 py-8">
        {/* Title and SortingControls */}
        <MediaGrid
          mediaItems={currentItems}
          itemsPerRow={itemsPerRow}
          openMediaViewer={openMediaViewer}
          type={type}
        />
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
        {showMediaViewer && (
          <MediaView
            initialIndex={selectedMediaIndex}
            onClose={closeMediaViewer}
            allMedia={sortedMedia.map((item) => item.src)}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            type={type}
          />
        )}
      </div>
    </div>
  );
}
```

## MediaGrid

Renders a grid of MediaCard components.

### Usage

```jsx
<MediaGrid
  mediaItems={currentItems}
  itemsPerRow={3}
  openMediaViewer={openMediaViewer}
  type="image"
/>
```

### Implementation

```jsx
export default function MediaGrid({
  mediaItems,
  itemsPerRow,
  openMediaViewer,
  type,
}: MediaGridProps) {
  if (mediaItems.length === 0) {
    return <div className="flex justify-center items-center h-96">
      <h1 className="text-2xl font-bold">No media found</h1>
    </div>;
  }

  return (
    <div className={`grid gap-4 md:gap-6 ${/* grid classes based on itemsPerRow */}`}>
      {mediaItems.map((item, index) => (
        <div key={index} onClick={() => openMediaViewer(index)} className="cursor-pointer">
          <MediaCard item={item} type={type} />
        </div>
      ))}
    </div>
  );
}
```

## MediaCard

Represents an individual media item in the grid.

### Usage

```jsx
<MediaCard item={mediaItem} type="image" />
```

### Implementation

```jsx
export default function MediaCard({ item, type }: MediaCardProps) {
  return (
    <div className="relative overflow-hidden rounded-lg shadow-lg group hover:shadow-xl hover:-translate-y-2 transition-transform duration-300 ease-in-out dark:bg-card dark:text-card-foreground">
      <a href="#" className="absolute inset-0 z-10">
        <span className="sr-only">View</span>
      </a>
      {type === "image" ? (
        <img
          src={item.src}
          alt={item.title}
          className="object-cover w-full h-64 transition-opacity duration-300"
        />
      ) : (
        <video
          controls
          src={item.src}
          className="object-cover w-full h-64 transition-opacity duration-300"
        />
      )}
    </div>
  );
}
```

## MediaView

Provides a full-screen view of media items with navigation.

### Usage

```jsx
<MediaView
  initialIndex={selectedMediaIndex}
  onClose={closeMediaViewer}
  allMedia={sortedMedia.map((item) => item.src)}
  currentPage={currentPage}
  itemsPerPage={itemsPerPage}
  type="image"
/>
```

### Implementation

```jsx
const MediaView: React.FC<MediaViewProps> = ({
  initialIndex,
  onClose,
  allMedia,
  currentPage,
  itemsPerPage,
  type,
}) => {
  const [globalIndex, setGlobalIndex] = useState<number>(
    (currentPage - 1) * itemsPerPage + initialIndex
  );

  // ... navigation handlers

  return (
    <div className="fixed top-0 left-0 w-full h-full flex justify-center items-center bg-black bg-opacity-90 z-50">
      <button onClick={onClose} className="absolute z-0 top-4 left-4 px-4 py-2 rounded-md border border-black bg-white text-black text-sm hover:shadow-[4px_4px_0px_0px_rgba(0,0,0)] transition duration-200">
        Back
      </button>
      {type === "image" ? (
        <img
          src={allMedia[globalIndex]}
          alt={`image-${globalIndex}`}
          className="max-h-full"
        />
      ) : (
        <video
          src={allMedia[globalIndex]}
          className="max-h-full"
          controls
          autoPlay
        />
      )}
      {/* Navigation buttons */}
    </div>
  );
};
```

## SortingControls

Provides sorting options for media items.

### Usage

```jsx
<SortingControls
  sortBy={sortBy}
  setSortBy={handleSetSortBy}
  mediaItems={mediaItems}
/>
```

### Implementation

```jsx
const SortingControls: React.FC<SortingControlsProps> = ({
  sortBy,
  setSortBy,
  mediaItems,
}) => {
  // ... year options generation logic

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="flex items-center gap-2">
          <ListOrderedIcon className="w-4 h-4" />
          Sort by {sortBy}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-[200px] bg-white dark:text-foreground"
        align="end"
      >
        <DropdownMenuRadioGroup value={sortBy} onValueChange={setSortBy}>
          <DropdownMenuRadioItem value="date">Date</DropdownMenuRadioItem>
          {yearOptions.map((option) => (
            <DropdownMenuRadioItem key={option.value} value={option.value}>
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

## Best Practices

1. Use TypeScript for type safety and better developer experience.
2. Implement proper error handling and loading states.
3. Optimize performance using React hooks like `useMemo` and `useCallback`.
4. Ensure accessibility in all components, especially in the MediaView for keyboard navigation.
5. Use Tailwind CSS for consistent and responsive styling.

This documentation provides an overview of the Gallery View components in your Tauri application. For more detailed information on specific components or functionalities, refer to the individual component files
