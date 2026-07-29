# Memories

Memories are curated collections of photos and short clips that the backend
scores and stores, and the frontend plays back as a full-screen, Instagram-style
story. The frontend never clusters or scores anything itself: it lists memories,
opens one, marks it viewed, and asks for a new curation run.

For how memories are produced — the schema, the three triggers and the scoring
signals — see [Memories (backend)](../backend/backend_python/memories.md).

## Routes and Pages

| Route               | Page component                      | Purpose                                     |
| ------------------- | ----------------------------------- | ------------------------------------------- |
| `memories`          | `pages/Memories/Memories.tsx`       | Grid of memory cards, plus the story viewer |
| `memories/settings` | `pages/Memories/MemorySettings.tsx` | Memory preferences                          |

Both are registered in `routes/AppRoutes.tsx`, with path names in
`constants/routes.ts` (`ROUTES.MEMORIES`, `ROUTES.MEMORIES_SETTINGS`).

## The Grid Page

`Memories.tsx` requests up to 60 cards and renders them in a responsive grid
(2 columns, up to 5 at `xl`).

- **Header** – Title, plus an "N new to look back on" line driven by
  `unviewed_count` from the status endpoint.
- **Refresh** – Requests a curation run. If the status snapshot reports
  `indexing_busy`, the click opens an info dialog instead of firing the request,
  because the backend declines to curate a half-indexed library.
- **Settings** – A gear button that navigates to the settings page.
- **Loading** – Ten pulsing placeholder tiles while the list query is in flight.
- **Empty state** – A dashed panel whose copy changes depending on whether a
  run is currently in progress.
- **Errors** – A failed list query is surfaced through the shared info dialog
  (`showInfoDialog`), not inline.

The page also mirrors the user's slide interval preference into the Redux slice
that the viewer reads, and renders `MemoryStoryViewer` whenever
`activeMemoryId` is set.

### MemoryCard

`components/Memories/MemoryCard.tsx` renders one tile as a `<button>`, so it is
focusable and keyboard-activatable. Each tile shows:

- The cover thumbnail (lazy loaded, scaling slightly on hover) over a gradient
  scrim that keeps the caption legible.
- A badge for the trigger type: `anniversary` reads "On this day",
  `import_event` reads "Event", `semantic_event` reads "Highlight".
- A dot beside the badge when `viewed_at` is still `null`.
- Title, subtitle and photo count, lifting on hover.

Covers and thumbnails resolve through `convertFileSrc()` and fall back to
`/photo.png` on load failure.

## The Story Viewer

`components/Memories/MemoryStoryViewer.tsx` is a full-screen `role="dialog"`
overlay. It fetches the full memory by id, merges its stills and clips into one
slide sequence, and plays through them.

### Progress and Autoplay

A row of segmented bars sits at the top — one per slide. Passed slides are
full, the active one fills live, later ones are empty.

`hooks/useStoryProgress.ts` drives the fill. It runs on
`requestAnimationFrame` and accumulates elapsed time in a ref, so pausing
resumes from where it stopped rather than restarting the slide. Changing the
slide index resets progress to zero; reaching 1 calls `onComplete`, which
advances the story.

Slide length is not uniform. `slideDurationMs()` gives a still the configured
photo interval, and gives a clip its own `duration` so the story neither cuts
away mid-shot nor holds a frozen last frame.

### Navigation

| Input                                     | Effect            |
| ----------------------------------------- | ----------------- |
| `ArrowRight` / right chevron / swipe left | Next slide        |
| `ArrowLeft` / left chevron / swipe right  | Previous slide    |
| `Space`                                   | Toggle play/pause |
| `Escape` / close button                   | Close the viewer  |

Swipes are measured on pointer events with a 50 px threshold, so a shorter drag
is ignored. Advancing past the last slide closes the viewer rather than
looping; going back from the first slide stays put.

The header also carries a play/pause button, a `current / total` counter, and a
gear that navigates to the settings page.

### Video Clips

A memory's videos arrive in their own array but share one `sort_order`
sequence with the images, so `buildMemorySlides()` merges rather than
concatenates them. Slides are a discriminated union (`{ kind: 'image' }` or
`{ kind: 'video' }`) because the two render as different elements.

Clips render as `<video autoPlay muted playsInline>` with the thumbnail as the
poster and no native controls — the story's own play/pause governs them. A
mute/unmute button appears in the corner on video slides only. Unmuting is a
per-slide choice: moving to another slide restores silence.

### Filmstrip

`components/Memories/MemoryFilmstrip.tsx` sits below the stage: a horizontally
scrolling `role="tablist"` of circular covers for jumping between memories
without leaving the viewer. The active memory has a white ring, unviewed ones a
primary-coloured ring, and already-viewed ones a faint one.

### Marking as Viewed

Opening a memory whose `viewed_at` is `null` fires a `PATCH` with
`{ viewed: true }`. It is guarded by memory id in a ref, so re-renders and
refetches do not repeat the mutation.

### Background Music

The viewer has a background-audio path gated on the `story_music_enabled`
preference (off by default): when enabled, a mute toggle appears in the header
and an `<audio loop>` element is mounted pointing at `/memory-theme.mp3`. An
audible clip mutes the theme so two soundtracks never overlap.

**The `memory-theme.mp3` asset is not shipped in `frontend/public/`, so the
theme is silent even with the preference on.**

## Settings

`MemorySettings.tsx` writes through `updateMemoriesPreferences()`, which patches
`user_preferences.memories`. Every control is disabled while a save is in
flight.

| Control               | Preference               | Range / default                          |
| --------------------- | ------------------------ | ---------------------------------------- |
| Generate memories     | `enabled`                | on                                       |
| Desktop notifications | `notifications_enabled`  | on; disabled unless memories are enabled |
| Background music      | `story_music_enabled`    | off                                      |
| Seconds per photo     | `slide_duration_seconds` | 1–15, default 5                          |
| Minimum photos        | `min_images`             | 2–20, default 5                          |
| Maximum photos        | `max_images`             | 5–100 step 5, default 30                 |

The two size sliders are clamped against each other on commit, since the
backend rejects a minimum above the maximum and would fail the whole save.

The seven scoring weights also live under `memories.weights` (defaults in
`hooks/useUserPreferences.tsx`) and can be patched through the same hook, but
this page does not expose an editor for them.

## Data Layer

Server state is React Query; Redux holds viewer UI state only.

### API Functions

`api/api-functions/memories.ts` holds the types (`MemoryCard`, `MemoryStory`,
`MemoryImage`, `MemoryVideo`, `MemoryStatusData`) and the fetchers. Endpoint
paths are centralised in `api/apiEndpoints.ts` as `memoriesEndpoints`.

| Function                         | Request                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| `getMemories(params)`            | `GET /memories` with `limit`, `offset`, `event_type`, `include_viewed`, `include_dismissed` |
| `getTodayMemory()`               | `GET /memories/today` — `data.memory` may be `null`                                         |
| `getMemory(id)`                  | `GET /memories/{id}` — the full story, images and videos                                    |
| `generateMemories(request)`      | `POST /memories/generate` with `{ force, reference_date }`                                  |
| `getMemoryStatus()`              | `GET /memories/status`                                                                      |
| `patchMemory({ memoryId, ... })` | `PATCH /memories/{id}` with `viewed`, `dismissed`, `notified`                               |
| `deleteMemory(id)`               | `DELETE /memories/{id}` — the underlying photos are untouched                               |

### Hooks

`hooks/useMemories.tsx` wraps those in `usePictoQuery` / `usePictoMutation`
under the `['memories']` key. Every query pins its payload generic explicitly so
`successData` stays typed.

| Hook                                     | Calls              | Notes                                                   |
| ---------------------------------------- | ------------------ | ------------------------------------------------------- |
| `useMemories(params)`                    | `getMemories`      | Backs the grid and filmstrip; 5-minute stale time       |
| `useTodayMemory()`                       | `getTodayMemory`   | The single memory to surface now                        |
| `useMemory(id)`                          | `getMemory`        | Disabled until an id is passed                          |
| `useMemoryStatus(enabled, forcePolling)` | `getMemoryStatus`  | Polls every 2 s while a run is running, or while forced |
| `useRefreshMemories()`                   | `generateMemories` | See below                                               |
| `useUpdateMemory()`                      | `patchMemory`      | Invalidates the `memories` key                          |
| `useDeleteMemory()`                      | `deleteMemory`     | Invalidates the `memories` key                          |

### Refresh Flow

`POST /memories/generate` returns once the run is _queued_, not once it has
finished, so `useRefreshMemories` follows the run instead of the response:

1. The mutation records the run start time already on file and turns on forced
   status polling, which covers the window before the worker writes `running`.
2. While a run is active — and once more on the transition out of it — only the
   `['memories', 'list']` key is invalidated, so results appear as they land.
   The `status` key is deliberately left alone; invalidating it would refetch
   the query driving the loop.
3. Forced polling stops when a run start time different from the recorded
   baseline appears, or the status reads `running`, or 90 s elapse. Keying on
   the start time rather than on catching `running` mid-flight matters for small
   libraries, where a run can begin and finish between two polls.

`isRefreshing` stays true from the click until the run settles, and drives both
the spinning icon and the disabled Refresh button.

### Redux Slice

`features/memoriesSlice.ts` holds viewer UI state and nothing else:
`activeMemoryId`, `slideIndex`, `isPlaying` (starts true), `isMuted` (starts
true) and `slideDurationMs` (default 5000, floored at 1000). `openMemory`
resets the index and starts playback; `closeMemory` clears the id and index.

### Formatting Helpers

`utils/memories.ts` is pure formatting plus slide assembly:

- `getMemoryImageUrl`, `getThumbnailUrl`, `getCoverUrl` – resolve stored paths
  through `convertFileSrc()`, falling back to `/photo.png`.
- `formatMemoryDate`, `formatDateRange` – locale dates; a range collapses to one
  date for a single day and to `12–14 July 2024` within a single month.
- `formatPhotoCount`, `formatEventType`, `formatMemorySubtitle` – card captions.
  The subtitle prefers the curator's own text, then the date span, then the
  surface date.
- `buildMemorySlides`, `slideDurationMs` – the merge and timing described above.

## Testing

- `components/Memories/__tests__/MemoryStoryViewer.test.tsx`
- `hooks/__tests__/useRefreshMemories.test.tsx`

## Related Documentation

- [Memories (backend)](../backend/backend_python/memories.md) – Schema,
  curation triggers and scoring.
- [State Management](state-management.md) – How the Redux store is organized.
- [Gallery View](gallery-view.md) – The main browsing experience.
- [UI Components](ui-components.md) – Shared components used across the app.
