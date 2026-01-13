import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchState {
  active: boolean;
  queryImage?: string;
  queryText?: string;
}

const initialState: SearchState = {
  active: false,
  queryImage: undefined,
  queryText: undefined,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startSearch(state, action: PayloadAction<string>) {
      state.active = true;
      // Check if payload is data URL or file path (basic check)
      if (action.payload.startsWith('data:') || action.payload.includes('/') || action.payload.includes('\\')) {
        state.queryImage = action.payload;
        state.queryText = undefined;
      } else {
        // Assume text query
        state.queryText = action.payload;
        state.queryImage = undefined;
      }
    },
    clearSearch(state) {
      state.active = false;
      state.queryImage = undefined;
      state.queryText = undefined;
    },
  },
});

export const { startSearch, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
