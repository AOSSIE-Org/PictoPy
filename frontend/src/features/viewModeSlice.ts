// src/features/viewModeSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type ViewMode = 'chronological' | 'grid' | 'list' | 'masonry';

interface ViewModeState {
  mode: ViewMode;
}

const initialState: ViewModeState = {
  mode: 'chronological',
};

const viewModeSlice = createSlice({
  name: 'viewMode',
  initialState,
  reducers: {
    setViewMode: (state, action: PayloadAction<ViewMode>) => {
      state.mode = action.payload;
    },
  },
});

export const { setViewMode } = viewModeSlice.actions;
export default viewModeSlice.reducer;
