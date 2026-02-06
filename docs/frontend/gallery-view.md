# Gallery View

The Gallery View is the heart of PictoPy, providing an intuitive and powerful interface for browsing, organizing, and managing your photo collection. Built with React and TypeScript, it offers a modern, responsive experience that adapts to different screen sizes and user preferences.

## Overview

The Gallery View presents photos in a chronological layout, automatically organizing images by date and providing smart navigation tools. It combines efficient rendering with rich metadata display and seamless integration with PictoPy's AI-powered features.

## Core Components

### ChronologicalGallery

The main gallery component (`ChronologicalGallery.tsx`) provides the primary photo browsing experience:

**Features:**
- **Chronological Organization**: Photos are automatically grouped by date (year/month)
- **Responsive Grid Layout**: Adapts to screen size with optimal thumbnail sizing
- **Virtual Scrolling**: Efficient rendering of large photo collections
- **Month Markers**: Visual separators between different time periods
- **Search Integration**: Seamlessly displays search results within the same interface

**Key Props:**
```typescript
interface ChronologicalGalleryProps {
  images: Image[];
  showTitle?: boolean;
  title?: string;
  onMonthOffsetsChange?: (markers: MonthMarker[]) => void;
  scrollContainerRef?: RefObject<HTMLDivElement>;
}
```

### ImageCard

Individual photo thumbnails (`ImageCard.tsx`) that display within the gallery:

**Features:**
- **Smart Thumbnails**: Optimized image loading with lazy loading
- **Metadata Overlay**: Shows key information on hover/selection
- **Selection States**: Visual feedback for selected images
- **Favorite Indicators**: Heart icons for favorited photos
- **AI Tags**: Displays detected objects, faces, and scenes
- **Quick Actions**: Context menu for common operations

**Interaction States:**
- **Default**: Clean thumbnail view
- **Hover**: Metadata overlay with quick actions
- **Selected**: Visual selection indicator
- **Loading**: Skeleton placeholder during image load

### Timeline Navigation

The Timeline Scrollbar (`TimelineScrollbar.tsx`) provides quick navigation through large photo collections:

**Features:**
- **Month Markers**: Visual indicators for each month with photos
- **Quick Jump**: Click to instantly navigate to specific time periods
- **Scroll Sync**: Automatically updates based on current scroll position
- **Responsive Design**: Adapts to different screen sizes

## Gallery Layouts

### Grid View (Default)

The primary gallery layout organizes photos in a responsive grid:

- **Adaptive Columns**: Automatically adjusts column count based on screen width
- **Consistent Spacing**: Maintains visual rhythm across different image sizes
- **Aspect Ratio Preservation**: Images maintain their original proportions
- **Smooth Scrolling**: Optimized for performance with large collections

### Chronological Grouping

Photos are automatically organized into logical time-based groups:

- **Year Sections**: Major separators for different years
- **Month Subsections**: Grouped by month within each year
- **Date Headers**: Clear visual indicators for time periods
- **Smart Spacing**: Appropriate gaps between different time periods

## Image Viewing Experience

### Full-Screen Viewer

The ImageViewer component (`ImageViewer.tsx`) provides an immersive viewing experience:

**Features:**
- **Full-Screen Display**: Maximizes image visibility
- **Zoom Controls**: Pinch-to-zoom and mouse wheel support
- **Pan Navigation**: Drag to explore zoomed images
- **Keyboard Shortcuts**: Arrow keys for navigation, ESC to close
- **Metadata Panel**: Detailed information sidebar
- **Navigation Controls**: Previous/next buttons with smooth transitions

### Media Controls

Comprehensive controls for image interaction (`MediaViewControls.tsx`):

- **Zoom In/Out**: Precise zoom control with zoom levels
- **Fit to Screen**: Automatic sizing options (fit, fill, actual size)
- **Rotation**: 90-degree rotation controls
- **Slideshow**: Automatic progression through images
- **Favorite Toggle**: Quick favorite/unfavorite action
- **Share Options**: Export and sharing functionality

## Search and Filtering

### Face Search Integration

The gallery seamlessly integrates with PictoPy's face recognition system:

- **Face-Based Filtering**: Show only photos containing specific people
- **Search Results Display**: Clear indication when viewing search results
- **Result Count**: Shows number of matching photos
- **Search State Management**: Maintains search context across navigation

### Smart Filtering

Advanced filtering options for photo organization:

- **Date Range**: Filter by specific time periods
- **AI Tags**: Filter by detected objects, scenes, or activities
- **Favorites**: Show only favorited photos
- **File Type**: Filter by image format (JPEG, PNG, RAW, etc.)
- **Folder Source**: Filter by source directory

## Performance Optimizations

### Efficient Rendering

The gallery is optimized for handling large photo collections:

- **Virtual Scrolling**: Only renders visible thumbnails
- **Lazy Loading**: Images load as they come into view
- **Progressive Enhancement**: Basic layout loads first, then enhancements
- **Memory Management**: Automatic cleanup of off-screen images

### Image Loading Strategy

Smart image loading for optimal performance:

- **Thumbnail Generation**: Server-side thumbnail creation
- **Progressive JPEG**: Loads low-quality first, then high-quality
- **Caching**: Intelligent browser and application-level caching
- **Preloading**: Anticipates next images in sequence

## Empty States

User-friendly empty states for different scenarios:

### EmptyGalleryState

Displayed when no photos are available:

- **Welcome Message**: Friendly introduction for new users
- **Action Buttons**: Direct links to add photos or configure folders
- **Visual Indicators**: Clear iconography and messaging
- **Onboarding Hints**: Guidance for getting started

### No Search Results

When search queries return no matches:

- **Clear Messaging**: Explains why no results were found
- **Search Suggestions**: Tips for refining search terms
- **Alternative Actions**: Links to browse all photos or try different searches

## Responsive Design

### Mobile Experience

Optimized for touch devices:

- **Touch-Friendly Targets**: Appropriately sized tap areas
- **Swipe Navigation**: Gesture-based image navigation
- **Mobile Grid**: Optimized column layout for small screens
- **Pull-to-Refresh**: Intuitive refresh gesture

### Desktop Experience

Enhanced for mouse and keyboard interaction:

- **Hover States**: Rich hover interactions with metadata
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Context Menus**: Right-click actions for power users
- **Multi-Selection**: Shift+click and Ctrl+click selection

## Accessibility Features

### Screen Reader Support

Full accessibility for visually impaired users:

- **Alt Text**: Descriptive text for all images
- **ARIA Labels**: Proper labeling for interactive elements
- **Focus Management**: Logical tab order and focus indicators
- **Semantic HTML**: Proper heading structure and landmarks

### Keyboard Navigation

Complete keyboard accessibility:

- **Tab Navigation**: All interactive elements are keyboard accessible
- **Arrow Key Navigation**: Navigate between images using arrow keys
- **Shortcut Keys**: Common actions available via keyboard shortcuts
- **Focus Indicators**: Clear visual focus indicators

## Integration with AI Features

### Object Detection

Visual indicators for AI-detected content:

- **Object Tags**: Overlay tags showing detected objects
- **Confidence Indicators**: Visual representation of detection confidence
- **Tag Filtering**: Click tags to filter similar images
- **Smart Grouping**: Automatic grouping by detected content

### Face Recognition

Seamless integration with face clustering:

- **Face Thumbnails**: Small face previews on image cards
- **Person Filtering**: Filter gallery by specific people
- **Face Collections**: Navigate to dedicated person views
- **Recognition Confidence**: Visual indicators for face match confidence

## Future Enhancements

### Planned Features

- **Map View**: Geographic organization of photos with location data
- **Timeline Scrubbing**: Smooth timeline navigation with preview thumbnails
- **Advanced Sorting**: Multiple sorting options (name, size, camera settings)
- **Batch Operations**: Multi-select actions for bulk photo management
- **Custom Albums**: User-created photo collections and albums

### Performance Improvements

- **WebGL Acceleration**: Hardware-accelerated image rendering
- **Service Worker Caching**: Offline gallery browsing capabilities
- **Predictive Loading**: AI-powered preloading based on user behavior
- **Compression Optimization**: Dynamic image quality based on network conditions

The Gallery View represents the culmination of modern web technologies and thoughtful UX design, providing users with an intuitive, powerful, and enjoyable way to explore their photo collections while leveraging PictoPy's advanced AI capabilities.