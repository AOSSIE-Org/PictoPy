# UI Components

PictoPy's frontend is built with React and TypeScript, featuring a comprehensive component library that provides a consistent and intuitive user interface. The application uses modern UI patterns with shadcn/ui components as the foundation.

## Component Architecture

The UI components are organized into several categories:

### Core UI Components (`/components/ui/`)

These are the foundational components based on shadcn/ui that provide consistent styling and behavior across the application.

#### Form Components
- **Button** (`button.tsx`) - Primary, secondary, and variant buttons with loading states
- **Input** (`input.tsx`) - Text input fields with validation styling
- **Label** (`label.tsx`) - Form labels with proper accessibility
- **Textarea** (`textarea.tsx`) - Multi-line text input
- **Switch** (`switch.tsx`) - Toggle switches for boolean settings
- **Radio Group** (`radio-group.tsx`) - Radio button groups for single selection
- **Slider** (`Slider.tsx`) - Range sliders for numeric input

#### Layout Components
- **Card** (`card.tsx`) - Container component for content sections
- **Dialog** (`dialog.tsx`) - Modal dialogs and popups
- **Sheet** (`sheet.tsx`) - Slide-out panels and drawers
- **Separator** (`separator.tsx`) - Visual dividers between content
- **Sidebar** (`sidebar.tsx`) - Navigation sidebar component
- **Scroll Area** (`scroll-area.tsx`) - Custom scrollable containers

#### Display Components
- **Avatar** (`avatar.tsx`) - User profile pictures and placeholders
- **Badge** (`badge.tsx`) - Status indicators and labels
- **Alert** (`alert.tsx`) - Notification and warning messages
- **Progress** (`progress.tsx`) - Progress bars and loading indicators
- **Skeleton** (`skeleton.tsx`) - Loading placeholders
- **Tooltip** (`tooltip.tsx`) - Contextual help and information

#### Navigation Components
- **Dropdown Menu** (`dropdown-menu.tsx`) - Context menus and action lists
- **Pagination** (`pagination.tsx`) - Page navigation controls
- **Pagination Controls** (`PaginationControls.tsx`) - Enhanced pagination with custom styling

#### Specialized Components
- **Aspect Ratio** (`aspect-ratio.tsx`) - Maintains consistent image/video ratios
- **Loading Screen** (`LoadingScreen/`) - Full-screen loading states
- **Error Page** (`ErrorPage/`) - Error handling and 404 pages
- **Icons** (`Icons/`) - Custom icon components and SVG assets

### Feature Components

#### Media Components (`/components/Media/`)

The media components handle the core photo viewing and management functionality:

- **ChronologicalGallery** (`ChronologicalGallery.tsx`) - Main gallery view with chronological organization
- **ImageCard** (`ImageCard.tsx`) - Individual photo thumbnails with metadata
- **ImageViewer** (`ImageViewer.tsx`) - Full-screen image viewing experience
- **ImageTags** (`ImageTags.tsx`) - AI-generated tags and metadata display
- **MediaView** (`MediaView.tsx`) - Unified media viewing component
- **MediaViewControls** (`MediaViewControls.tsx`) - Playback and navigation controls
- **MediaThumbnails** (`MediaThumbnails.tsx`) - Thumbnail grid layouts
- **MediaInfoPanel** (`MediaInfoPanel.tsx`) - Detailed media information sidebar
- **NavigationButtons** (`NavigationButtons.tsx`) - Previous/next navigation
- **ZoomControls** (`ZoomControls.tsx`) - Image zoom and pan controls

#### Navigation Components (`/components/Navigation/`)

Handles application navigation and routing:

- Main navigation sidebar
- Breadcrumb navigation
- Tab navigation for different views

#### Dialog Components (`/components/Dialog/`)

Modal dialogs for various interactions:

- Confirmation dialogs
- Settings dialogs
- Information displays

#### Specialized Feature Components

- **FaceCollections** (`FaceCollections.tsx`) - Face recognition clustering interface
- **ThemeToggle** (`ThemeToggle.tsx`) - Dark/light mode switcher
- **Timeline** (`Timeline/TimelineScrollbar.tsx`) - Chronological navigation
- **FolderPicker** (`FolderPicker/`) - Directory selection interface
- **Loader** (`Loader/`) - Application-wide loading states
- **OnboardingSteps** (`OnboardingSteps/`) - User onboarding flow
- **VideoPlayer** (`VideoPlayer/`) - Video playback component
- **WebCam** (`WebCam/`) - Camera integration for photo capture
- **Updater** (`Updater/`) - Application update notifications

### Empty States (`/components/EmptyStates/`)

Provides user-friendly empty state components when no content is available:

- Empty gallery states
- No search results
- Missing folder content

## Component Design Principles

### 1. Consistency
All components follow consistent design patterns using a shared design system based on shadcn/ui, ensuring visual harmony across the application.

### 2. Accessibility
Components are built with accessibility in mind, including:
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Focus management

### 3. Responsiveness
All components are designed to work across different screen sizes:
- Mobile-first approach
- Flexible layouts
- Touch-friendly interactions

### 4. Performance
Components are optimized for performance:
- Lazy loading for images
- Virtual scrolling for large lists
- Memoization for expensive operations
- Efficient re-rendering patterns

### 5. Type Safety
Full TypeScript integration provides:
- Compile-time error checking
- IntelliSense support
- Better developer experience
- Reduced runtime errors

## Styling System

### CSS Framework
The application uses Tailwind CSS for styling, providing:
- Utility-first approach
- Consistent spacing and colors
- Responsive design utilities
- Dark mode support

### Theme System
PictoPy supports both light and dark themes:
- Automatic system preference detection
- Manual theme switching
- Consistent color schemes
- Smooth transitions between themes

### Component Variants
Many components support multiple variants:
- **Buttons**: primary, secondary, outline, ghost, destructive
- **Alerts**: default, destructive, warning, success
- **Badges**: default, secondary, outline, destructive

## Usage Examples

### Basic Button Usage
```typescript
import { Button } from "@/components/ui/button";

<Button variant="primary" size="lg" onClick={handleClick}>
  Upload Photos
</Button>
```

### Image Card in Gallery
```typescript
import { ImageCard } from "@/components/Media/ImageCard";

<ImageCard
  image={imageData}
  onSelect={handleImageSelect}
  isSelected={isSelected}
  showMetadata={true}
/>
```

### Dialog with Form
```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Add New Album</DialogTitle>
    </DialogHeader>
    <div className="space-y-4">
      <Input placeholder="Album name" value={name} onChange={setName} />
      <Button onClick={handleSave}>Create Album</Button>
    </div>
  </DialogContent>
</Dialog>
```

## Component Testing

Components are tested using:
- **Jest** for unit testing
- **React Testing Library** for component testing
- **TypeScript** for type checking
- **ESLint** for code quality

Test files are located in `__tests__` directories alongside components, ensuring comprehensive coverage of component functionality and user interactions.

## Development Guidelines

### Creating New Components
1. Use TypeScript for all components
2. Follow the existing naming conventions
3. Include proper prop types and interfaces
4. Add accessibility attributes
5. Write comprehensive tests
6. Document component props and usage

### Component Structure
```typescript
interface ComponentProps {
  // Define all props with proper types
}

export const Component: React.FC<ComponentProps> = ({
  // Destructure props
}) => {
  // Component logic
  
  return (
    // JSX with proper accessibility
  );
};
```

This component architecture ensures PictoPy provides a smooth, accessible, and performant user experience while maintaining code quality and developer productivity.