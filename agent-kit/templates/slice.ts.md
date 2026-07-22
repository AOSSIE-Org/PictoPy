# Template: `frontend/src/features/<feature>Slice.ts`

Copy and adapt. Modelled on `frontend/src/features/videoSlice.ts`.

```ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Item } from '@/types/Media';

interface FeatureState {
  items: Item[];
  currentViewIndex: number;
}

const initialState: FeatureState = {
  items: [],
  currentViewIndex: -1,
};

const featureSlice = createSlice({
  name: 'feature',
  initialState,
  reducers: {
    setItems(state, action: PayloadAction<Item[]>) {
      state.items = action.payload;
    },

    setCurrentViewIndex(state, action: PayloadAction<number>) {
      const index = action.payload;
      // The reducer owns validity; callers don't bounds-check before dispatching.
      if (index >= -1 && index < state.items.length) {
        state.currentViewIndex = index;
      } else {
        console.warn(
          `Invalid index: ${index}. Valid range: -1 to ${state.items.length - 1}`,
        );
      }
    },

    closeView(state) {
      state.currentViewIndex = -1;
    },
  },
});

export const { setItems, setCurrentViewIndex, closeView } = featureSlice.actions;
export default featureSlice.reducer;
```

Selectors go in a sibling `<feature>Selectors.ts`:

```ts
import { RootState } from '@/app/store';

export const selectItems = (state: RootState) => state.feature.items;

export const selectCurrentItem = (state: RootState) =>
  state.feature.currentViewIndex >= 0
    ? state.feature.items[state.feature.currentViewIndex]
    : null;
```

## Notes

- Reducers are **total**: validate indices and ranges inside the reducer, warn and no-op on
  bad input. Callers dispatch without pre-checking.
- `-1` is the convention for "nothing selected" in this codebase, not `null`.
- Derived data goes in selectors, never computed inline in a component.
- Register the reducer in the store under `frontend/src/store/`.
- Import types through `@/`, which resolves to `frontend/src`.
