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
    setSearchQuery(state, action: PayloadAction<string>) {
      state.queryText = action.payload;
    },
    startSearch(state, action: PayloadAction<string>) {
      state.active = true;
      const query = action.payload.trim();

      // Improved path detection
      const isPath = query.startsWith('data:') ||
        (query.length > 3 && (query.includes('/') || query.includes('\\')) && /\.(jpg|jpeg|png|webp|gif)$/i.test(query));

      if (isPath) {
        state.queryImage = query;
        state.queryText = undefined;
      } else {
        state.queryText = query;
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

export const { startSearch, clearSearch, setSearchQuery } = searchSlice.actions;
export default searchSlice.reducer;
