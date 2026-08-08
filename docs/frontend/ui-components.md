# UI Components

PictoPy’s frontend uses a mix of shared primitives (based on ShadCN) and app-specific components. This page gives an overview of both so you can find and reuse the right parts when building or changing the UI.

## Overview

- **Primitives** live under `components/ui/` and provide buttons, inputs, dialogs, and other low-level building blocks.
- **Feature components** implement gallery, onboarding, navigation, and media behaviour and often use these primitives.

## ShadCN-style primitives (`components/ui/`)

These are the base components used across the app:

| Component       | Role                                            |
| --------------- | ----------------------------------------------- |
| `button`        | Buttons with variants (default, outline, ghost) |
| `card`          | Card container with header, content, footer     |
| `dialog`        | Modal dialogs                                   |
| `input`         | Text inputs                                     |
| `label`         | Form labels                                     |
| `textarea`      | Multi-line text input                           |
| `badge`         | Tags and status badges                          |
| `alert`         | Inline alerts and messages                      |
| `avatar`        | User or entity avatars                          |
| `dropdown-menu` | Dropdown menus                                  |
| `scroll-area`   | Custom scrollable areas                         |
| `sidebar`       | App sidebar layout                              |
| `sheet`         | Slide-out panels                                |
| `separator`     | Visual dividers                                 |
| `slider`        | Slider for volume, video-duration, etc.         |
| `switch`        | Toggle switches                                 |
| `radio-group`   | Radio button groups                             |
| `pagination`    | Pagination controls                             |
| `progress`      | Progress bars                                   |
| `skeleton`      | Loading skeletons                               |
| `tooltip`       | Hover tooltips                                  |
| `aspect-ratio`  | Fixed aspect-ratio wrapper                      |

App-specific UI pieces in the same area:

- **404** – Not-found page layout
- **ErrorPage** – Full-page error view
- **LoadingScreen** – App loading screen
- **Icons** – Shared icon set
- **PaginationControls** – Pagination tuned for the gallery

## Feature components

These implement specific features and often use the primitives above:

### Media and gallery

- **Media/** – `ChronologicalGallery`, `ImageCard`, `ImageViewer`, `MediaView`, `MediaThumbnails`, `MediaInfoPanel`, `MediaViewControls`, `ZoomControls`, `NavigationButtons`, `ImageTags`
- **FaceCollections** – Face clusters and naming UI

### Navigation and layout

- **Navigation/Navbar** – Top app bar
- **Navigation/Sidebar** – App sidebar (e.g. `AppSidebar`)

### Onboarding and settings

- **OnboardingSteps/** – Steps, folder setup, avatar choice, theme selection, server check, etc.
- **account-settings** – User account and preference UI

### Dialogs and feedback

- **Dialog/** – `InfoDialog`, `FaceSearchDialog`
- **Loader/** – `GlobalLoader`
- **EmptyStates/** – `EmptyGalleryState`, `EmptyAITaggingState`

### Search

- **SearchResults** (`pages/SearchResults/`) – Single search results page for
  both tag search and semantic search (no separate mode toggle in the UI).
  Tries an exact tag match first; falls back to semantic search only when
  that returns zero results and the feature is installed. Renders results
  through the same `ImageCard`/`MediaView` components as the rest of the
  gallery — a `ScoredImage` (an `Image` plus a `score`) carries the match
  score end-to-end, but it is never rendered; sorting happens on the
  backend before the response is returned.

### Model Manager

- **ModelManager** (`pages/ModelManager/`) – Install/uninstall UI for all
  optional AI model tiers, including the ~1.5 GB "Semantic Search" (SigLIP2)
  bundle alongside the existing YOLO/FaceNet tiers.
  - **AvailableTab** – Shows tiers/bundles not yet fully installed, with
    per-model download progress. The semantic bundle card only appears when
    at least one of its three files is missing.
  - **InstalledTab** – Shows fully installed tiers/bundles with
    set-active/uninstall actions. Uninstalling the semantic bundle removes
    all three files (vision, text, tokenizer) via `Promise.allSettled`, so a
    partial failure lands back in "Available" with a "Needs Repair" badge
    rather than silently losing track of the partial state.
  - Both tabs derive the semantic bundle's model keys and display text from
    shared constants in `types/models.ts` (`SEMANTIC_BUNDLE_KEYS`,
    `SEMANTIC_BUNDLE_TITLE`/`LABEL`/`DESCRIPTION`) rather than duplicating
    them per-component.

### Memories

Story-style browsing of curated memories. The pages own layout and data
fetching; the components under `components/Memories/` are presentational and
take everything they render as props.

- **Memories** (`pages/Memories/Memories.tsx`) – The grid page. Loads cards
  with `useMemories({ limit: 60 })` and renders a responsive grid (2 columns
  up to 5 at `xl`), with pulsing skeletons while loading and an empty state
  otherwise. A "Refresh" button calls `useRefreshMemories`; when
  `/memories/status` reports `indexing_busy` it shows an info dialog instead of
  starting a run. A gear button routes to `memories/settings`. It mirrors the
  `slide_duration_seconds` preference into the Redux slice as milliseconds, and
  mounts `MemoryStoryViewer` whenever `activeMemoryId` is set.
- **MemorySettings** (`pages/Memories/MemorySettings.tsx`) – Settings page for
  the `memories` user preferences, read and written through
  `useUserPreferences`. A local `ToggleRow` renders the switches ("Generate
  memories", "Desktop notifications", "Background music"); sliders cover
  seconds per photo (1–15), minimum photos (2–20) and maximum photos (5–100,
  in steps of 5). The two size sliders clamp each other so the minimum can
  never be committed above the maximum. Switches write on change; sliders write
  on `onValueCommit`, so dragging one does not fire a request per step. Every
  control is disabled while a save is in flight.
- **MemoryCard** (`components/Memories/MemoryCard.tsx`) – Grid tile, props
  `{ memory: MemoryCard; onOpen: (memoryId: string) => void }`. A 4:5 button
  showing the cover with a gradient scrim, an event-type `badge`, a dot when
  `viewed_at` is `null`, the title, subtitle and photo count. The cover scales
  and the caption lifts on hover.
- **MemoryStoryViewer** (`components/Memories/MemoryStoryViewer.tsx`) –
  Full-screen viewer, props
  `{ memoryId: string; memories: MemoryCard[]; musicEnabled: boolean }`.
  Fetches the story with `useMemory` and merges its stills and clips into one
  chronological slide list via `buildMemorySlides`. Highlights:
  - Segmented progress bars, one per slide, with the active bar filling live
    from `useStoryProgress`.
  - Navigation by arrow buttons, `ArrowLeft`/`ArrowRight`, and pointer swipe
    (50 px of horizontal travel counts as a swipe rather than a tap). `Space`
    toggles play/pause, `Escape` closes. Advancing past the last slide closes
    the viewer rather than looping.
  - Image slides render as `<img>`; video slides render as a `<video autoPlay
muted playsInline>` with no native controls, following the story's own
    play/pause. A per-clip sound button unmutes the current clip only — the
    slide reverts to silent when you move on.
  - Opening a memory marks it viewed once, through `useUpdateMemory`.
  - It embeds `MemoryFilmstrip` so you can jump between memories in place.
  - `musicEnabled` (the `story_music_enabled` preference) gates the mute
    button and a looping `<audio>` element. No soundtrack file ships with the
    app, so that element currently produces no sound.
- **MemoryFilmstrip** (`components/Memories/MemoryFilmstrip.tsx`) – Horizontal
  strip of circular covers, props
  `{ memories: MemoryCard[]; activeMemoryId: string | null; onSelect: (memoryId: string) => void }`.
  Renders as a `tablist`; the ring around each cover marks the active memory,
  an unviewed one, or neither. Renders nothing when the list is empty.
- **useStoryProgress** (`hooks/useStoryProgress.ts`) – The hook driving the
  progress bars. Takes `{ index, durationMs, isPlaying, onComplete }` and
  returns progress through the current slide as a number from 0 to 1. It runs
  on `requestAnimationFrame`, resets whenever `index` changes, and preserves
  elapsed time across a pause so resuming does not restart the slide.

Viewer state (`activeMemoryId`, `slideIndex`, `isPlaying`, `isMuted`,
`slideDurationMs`) lives in `features/memoriesSlice.ts`; the memories
themselves come from React Query.

### Other

- **FolderPicker/** – Folder selection and related dialogs (e.g. `DeleteImageDialog`)
- **ThemeToggle** – Light/dark theme switch
- **Timeline/** – `TimelineScrollbar`
- **Updater/** – `UpdateDialog`
- **VideoPlayer/** – `NetflixStylePlayer`
- **WebCam/** – `WebCamComponent`

## Styling

UI components are styled with **Tailwind CSS**. Shared look and behaviour (including themes) are kept consistent via Tailwind classes and the design tokens used by the ShadCN-based components.

## Related documentation

- [Gallery View](gallery-view.md) – How the main gallery is built from these components
- [Memories](memories.md) – The memories pages, hooks and API layer in full
- [State Management](state-management.md) – How components connect to Redux
- [Screenshots](screenshots.md) – Screenshots of the app using these components
