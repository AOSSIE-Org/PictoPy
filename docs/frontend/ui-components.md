# UI Components

PictoPy’s frontend uses a mix of shared primitives (based on ShadCN) and app-specific components. This page gives an overview of both so you can find and reuse the right parts when building or changing the UI.

## Overview

- **Primitives** live under `components/ui/` and provide buttons, inputs, dialogs, and other low-level building blocks.
- **Feature components** implement gallery, onboarding, navigation, and media behaviour and often use these primitives.

## ShadCN-style primitives (`components/ui/`)

These are the base components used across the app:

| Component      | Role                                             |
|----------------|--------------------------------------------------|
| `button`       | Buttons with variants (default, outline, ghost)  |
| `card`         | Card container with header, content, footer      |
| `dialog`       | Modal dialogs                                    |
| `input`        | Text inputs                                      |
| `label`        | Form labels                                      |
| `textarea`     | Multi-line text input                            |
| `badge`        | Tags and status badges                           |
| `alert`        | Inline alerts and messages                       |
| `avatar`       | User or entity avatars                           |
| `dropdown-menu`| Dropdown menus                                   |
| `scroll-area`  | Custom scrollable areas                          |
| `sidebar`      | App sidebar layout                               |
| `sheet`        | Slide-out panels                                 |
| `separator`    | Visual dividers                                  |
| `slider`       | Slider for volume, video-duration, etc.          |
| `switch`       | Toggle switches                                  |
| `radio-group`  | Radio button groups                              |
| `pagination`   | Pagination controls                              |
| `progress`     | Progress bars                                    |
| `skeleton`     | Loading skeletons                                |
| `tooltip`      | Hover tooltips                                   |
| `aspect-ratio` | Fixed aspect-ratio wrapper                       |

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
- [State Management](state-management.md) – How components connect to Redux
- [Screenshots](screenshots.md) – Screenshots of the app using these components
