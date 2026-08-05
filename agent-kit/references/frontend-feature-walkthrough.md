# Frontend feature walkthrough

The video feature traced from state to screen. Read it before adding a feature.

## The files

```text
frontend/src/types/Media.ts                    # the Video type
frontend/src/api/apiEndpoints.ts               # videosEndpoints
frontend/src/api/api-functions/videos.ts       # typed call wrappers
frontend/src/features/videoSlice.ts            # Redux state
frontend/src/features/videoSelectors.ts        # derived data
frontend/src/hooks/useToggleVideoFav.ts        # the bridge components use
frontend/src/components/VideoPlayer/           # presentation
frontend/src/features/__tests__/videoSlice.test.ts
```

## API layer — two files, always both

`apiEndpoints.ts` holds URLs and nothing else, grouped per resource:

```ts
export const videosEndpoints = {
  getAllVideos: '/videos/',
  setFavourite: '/videos/toggle-favourite',
};
```

Parameterised URLs are functions that encode their arguments — from `imagesEndpoints`:

```ts
searchByTag: (tag: string) => `/images/search?tag=${encodeURIComponent(tag)}`,
```

`api-functions/videos.ts` wraps each one with a type:

```ts
export const fetchAllVideos = async (): Promise<APIResponse> => {
  const response = await apiClient.get<APIResponse>(videosEndpoints.getAllVideos);
  return response.data;
};
```

`apiClient` comes from `../axiosConfig` and carries the base URL and interceptors. A
component importing `axios` directly means this wrapper is missing.

## State

`videoSlice.ts` is a plain Redux Toolkit `createSlice`. The convention worth copying is
that reducers are **total** — they validate rather than trusting the caller:

```ts
setCurrentViewIndex(state, action: PayloadAction<number>) {
  const videoList = state.videos;
  const index = action.payload;
  if (index >= -1 && index < videoList.length) {
    state.currentViewIndex = index;
  } else {
    console.warn(`Invalid video index: ${index}. ...`);
  }
}
```

Callers do not bounds-check before dispatching. Keep that contract: the reducer owns
validity.

Derived data belongs in `videoSelectors.ts`, not computed inside components.

## Hooks

`src/hooks/` is where components get data. Hooks combine the API wrappers with the store
and, in places, React Query (`useQueryExtension.ts`, `useMutationFeedback.tsx`). Follow
whichever pattern the neighbouring feature uses — the codebase mixes React Query and plain
Redux thunks, and adding a third approach makes it worse.

## Components

- `src/components/ui/` is shadcn-generated. Regenerate, never hand-edit.
- Tailwind v4; `prettier-plugin-tailwindcss` sorts class names, so never order them by hand.
- Import via `@/`, which `tsconfig.json` maps to `frontend/src`.

## Tests

`features/__tests__/videoSlice.test.ts` tests the reducer directly — dispatch an action
against a known state, assert the next state. Component tests in
`components/__tests__/` use React Testing Library and assert on rendered output.

Empty states are worth a test of their own; `EmptyStates.test.tsx` exists because they have
regressed before.
