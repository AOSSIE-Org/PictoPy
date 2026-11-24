import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { MAX_SELECTED_FACES } from '@/utils/faceSearch';
import type { FaceMatchMode } from '@/types/Media';

export interface FaceSelection {
  /** Positions in the face list that detect-faces returned for the query photo. */
  indices: number[];
  matchMode: FaceMatchMode;
}

interface SearchState {
  queryImage?: string;
  // Set once the user has picked faces; a photo with one face never needs it.
  faceSelection?: FaceSelection;
}

const initialState: SearchState = {
  queryImage: undefined,
  faceSelection: undefined,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startSearch(state, action: PayloadAction<string>) {
      state.queryImage = action.payload;
      // A new photo must not inherit the faces picked in the old one.
      state.faceSelection = undefined;
    },
    clearSearch(state) {
      state.queryImage = undefined;
      state.faceSelection = undefined;
    },
    setFaceSelection(state, action: PayloadAction<FaceSelection>) {
      const indices = [...new Set(action.payload.indices)]
        .filter((index) => Number.isInteger(index) && index >= 0)
        .slice(0, MAX_SELECTED_FACES);
      if (indices.length === 0) return;
      state.faceSelection = {
        indices,
        // One face has nothing to combine, and any/all agree on it.
        matchMode: indices.length > 1 ? action.payload.matchMode : 'match_any',
      };
    },
    clearFaceSelection(state) {
      state.faceSelection = undefined;
    },
  },
});

export const {
  startSearch,
  clearSearch,
  setFaceSelection,
  clearFaceSelection,
} = searchSlice.actions;
export default searchSlice.reducer;
