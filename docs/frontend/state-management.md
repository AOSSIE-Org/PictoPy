# State Management with Redux

This guide outlines the Redux-based state management system used in our PictoPy application, focusing on Redux slices and store configuration.

## Overview

Our application uses Redux Toolkit for state management, which provides:

- **Redux slices** for feature-based state organization
- **Immutable state updates** with Immer
- **TypeScript integration** for type safety

The Redux store serves as the single source of truth for application state that needs to be shared across multiple components.

## Store Structure

Our Redux store is organized into the following slices:

### 1. Images Slice

Manages the state for images and media viewing operations.

**State Structure:**

```typescript
interface ImageState {
  images: Image[];
  currentViewIndex: number;
  totalImages: number;
  error: string | null;
}
```

**Key Actions:**

- `setImages` - Updates the images array
- `addImages` - Adds new images to the array
- `setCurrentViewIndex` - Sets the currently viewed image index
- `nextImage` - Navigates to the next image
- `previousImage` - Navigates to the previous image
- `closeImageView` - Closes the image viewer
- `updateImage` - Updates specific image data
- `removeImage` - Removes an image from the array
- `setError` - Sets error state
- `clearImages` - Clears all image data

### 2. Folders Slice

Manages folder-related state and operations.

**State Structure:**

```typescript
interface FolderState {
  folders: FolderDetails[];
}
```

**Key Actions:**

- `setFolders` - Updates the folders array
- `addFolder` - Adds a new folder or updates existing one
- `updateFolder` - Modifies an existing folder
- `removeFolders` - Removes folders by IDs
- `clearFolders` - Clears all folder data

### 3. Face Clusters Slice

Handles face recognition clusters and naming.

**State Structure:**

```typescript
interface FaceClustersState {
  clusters: Cluster[];
}
```

**Key Actions:**

- `setClusters` - Updates the clusters array
- `updateClusterName` - Updates a cluster's name

### 4. Onboarding Slice

Manages the user onboarding process and user profile.

**State Structure:**

```typescript
interface OnboardingState {
  currentStepIndex: number;
  currentStepName: string;
  stepStatus: boolean[];
  avatar: string | null;
  name: string;
}
```

**Key Actions:**

- `setAvatar` - Sets user avatar
- `setName` - Sets user name
- `markCompleted` - Marks an onboarding step as completed
- `previousStep` - Goes back to the previous onboarding step

### 5. Loader Slice

Manages loading states across the application.

**State Structure:**

```typescript
interface LoaderState {
  loading: boolean;
  message: string;
}
```

**Key Actions:**

- `showLoader` - Shows loading state with message
- `hideLoader` - Hides loading state

### 6. Info Dialog Slice

Manages information dialog display and content.

**State Structure:**

```typescript
interface InfoDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  variant: InfoDialogVariant;
  showCloseButton: boolean;
}
```

**Key Actions:**

- `showInfoDialog` - Shows information dialog with content
- `hideInfoDialog` - Hides information dialog

## Redux Toolkit Configuration

### Store Setup

```typescript
import { configureStore } from "@reduxjs/toolkit";
import loaderReducer from "@/features/loaderSlice";
import onboardingReducer from "@/features/onboardingSlice";
import imageReducer from "@/features/imageSlice";
import faceClustersReducer from "@/features/faceClustersSlice";
import infoDialogReducer from "@/features/infoDialogSlice";
import folderReducer from "@/features/folderSlice";

export const store = configureStore({
  reducer: {
    loader: loaderReducer,
    onboarding: onboardingReducer,
    images: imageReducer,
    faceClusters: faceClustersReducer,
    infoDialog: infoDialogReducer,
    folders: folderReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

## Usage in Components

### Connecting Components

Use the `useSelector` and `useDispatch` hooks to connect components to the Redux store:

```typescript
import { useSelector, useDispatch } from "react-redux";
import { RootState, AppDispatch } from "../app/store";
import { setImages, nextImage } from "../features/imageSlice";
import { showLoader, hideLoader } from "../features/loaderSlice";

const ImageViewer = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { images, currentViewIndex } = useSelector(
    (state: RootState) => state.images
  );
  const { loading, message } = useSelector((state: RootState) => state.loader);

  const handleNextImage = () => {
    dispatch(nextImage());
  };

  // Component logic...
};
```

### Typed Hooks

For better TypeScript support, we use typed versions of the hooks:

```typescript
import { useDispatch, useSelector, TypedUseSelectorHook } from "react-redux";
import type { RootState, AppDispatch } from "../app/store";

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

## Best Practices

1. **Keep slices focused** - Each slice should manage a specific domain of your application
2. **Normalize state shape** - Use normalized data structures for complex relational data
3. **Use selectors** - Create reusable selectors for complex state derivations (see `folderSelectors.ts`, `imageSelectors.ts`, `onboardingSelectors.ts`)

## Selectors

The application uses dedicated selector files for complex state derivations:

- `folderSelectors.ts` - Folder-related selectors
- `imageSelectors.ts` - Image-related selectors
- `onboardingSelectors.ts` - Onboarding state selectors

Example selector usage:

```typescript
import { getFolderById } from "@/features/folderSelectors";

const folder = useSelector((state: RootState) =>
  getFolderById(state, folderId)
);
```

This Redux-based architecture provides a scalable and maintainable state management solution that grows with our application's complexity.
