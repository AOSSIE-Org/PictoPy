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

### 7. Memories Slice

Holds story-viewer UI state only. The memories themselves are server state and live in React Query (see [Server State with React Query](#server-state-with-react-query)).

**State Structure:**

```typescript
interface MemoriesState {
  activeMemoryId: string | null;
  slideIndex: number;
  isPlaying: boolean;
  isMuted: boolean;
  slideDurationMs: number;
}
```

The initial state opens no memory (`activeMemoryId: null`), starts playing, starts muted, and uses `DEFAULT_SLIDE_DURATION_MS` (5000) for `slideDurationMs`.

**Key Actions:**

- `openMemory` - Opens a memory by id, resetting the slide index and resuming playback
- `closeMemory` - Closes the viewer and resets the slide index
- `setSlideIndex` - Sets the current slide (clamped to a minimum of `0`)
- `setPlaying` - Sets playback on or off
- `togglePlaying` - Flips playback
- `setMuted` - Sets the muted flag
- `toggleMuted` - Flips the muted flag
- `setSlideDuration` - Sets the slide duration (clamped to a minimum of `1000` ms)
- `resetMemories` - Restores the initial state

**Selectors:** `memoriesSlice.ts` exports its own selectors rather than using a separate file - `selectActiveMemoryId`, `selectSlideIndex`, `selectIsPlaying`, `selectIsMuted` and `selectSlideDurationMs`.

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
import memoriesReducer from "@/features/memoriesSlice";

export const store = configureStore({
  reducer: {
    loader: loaderReducer,
    onboarding: onboardingReducer,
    images: imageReducer,
    faceClusters: faceClustersReducer,
    infoDialog: infoDialogReducer,
    folders: folderReducer,
    memories: memoriesReducer,
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
    (state: RootState) => state.images,
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

## Server State with React Query

Data that comes from the backend is not kept in Redux. It is fetched and cached with React Query through the two wrappers in `hooks/useQueryExtension.ts`:

- `usePictoQuery` - wraps `useQuery`, and unwraps the `{ success, message, data }` backend envelope into `successData`, `successMessage` and `errorMessage`
- `usePictoMutation` - wraps `useMutation` with the same unwrapping, plus an `autoInvalidateTags` option that invalidates a query key once the mutation settles

Memories follow this split exactly: every memory record is read through React Query, while the Redux `memories` slice above carries only the viewer's UI state.

### Memories Hooks

All memories hooks live in `hooks/useMemories.tsx` and share the base key `MEMORIES_QUERY_KEY = ["memories"]`.

| Hook                                       | Kind     | Fetches                                                                           | Query key                            | Stale time             |
| ------------------------------------------ | -------- | --------------------------------------------------------------------------------- | ------------------------------------ | ---------------------- |
| `useMemories(params?)`                     | Query    | Memory cards for the grid and filmstrip (`memories`, `total_count`)               | `["memories", "list", params ?? {}]` | 5 minutes              |
| `useTodayMemory()`                         | Query    | The memory to surface now; `successData.memory` may be `null`                     | `["memories", "today"]`              | 5 minutes              |
| `useMemory(memoryId?)`                     | Query    | One memory with its images and videos; disabled until an id is passed             | `["memories", "detail", memoryId]`   | 5 minutes              |
| `useMemoryStatus(enabled?, forcePolling?)` | Query    | The scheduler snapshot (run status, unviewed count, whether memories are enabled) | `["memories", "status"]`             | Default; polls instead |
| `useUpdateMemory()`                        | Mutation | `PATCH` of `viewed` / `dismissed` / `notified`                                    | Invalidates `["memories"]`           | -                      |
| `useDeleteMemory()`                        | Mutation | Deletes a memory; the underlying photos are untouched                             | Invalidates `["memories"]`           | -                      |

`useMemoryStatus` sets `refetchInterval` to `RUN_POLL_INTERVAL_MS` (2000 ms) while `forcePolling` is set or the reported `run_status` is `"running"`, and to `false` otherwise.

### `useRefreshMemories`

`POST /memories/generate` returns once the curation run is **queued**, not once it has finished, so this hook follows the run instead of the response. It combines a `usePictoMutation` over `generateMemories` with `useMemoryStatus`:

1. On a successful `POST` it records the run start time already on file and turns on force-polling, so `/memories/status` is polled every 2 s from the click rather than only after a `"running"` status happens to appear.
2. While the run is active - and once more on the tick after it stops being active - it invalidates only `["memories", "list"]`, so results land in the grid as they are written. The `"status"` key that drives the polling loop is never invalidated.
3. Force-polling stops when `run_started_at` differs from the recorded baseline, when the status reads `"running"`, or after `RUN_START_TIMEOUT_MS` (90 s), whichever comes first.

It returns `refresh(force = true)`, `isRefreshing` (true from the click until the run settles, not just until it is queued) and the underlying `status` query.

See [Memories](memories.md) for the components that consume these hooks.

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
  getFolderById(state, folderId),
);
```

This Redux-based architecture provides a scalable and maintainable state management solution that grows with our application's complexity.
