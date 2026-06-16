import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchState {
  active: boolean;
  queryImage?: string;
  tagQuery: string;
}

const initialState: SearchState = {
  active: false,
  queryImage: undefined,
  tagQuery: '',
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startSearch(state, action: PayloadAction<string>) {
      state.active = true;
      state.queryImage = action.payload;
    },

    clearSearch(state) {
      state.active = false;
      state.queryImage = undefined;
    },

    setTagSearchQuery(state, action: PayloadAction<string>) {
      state.tagQuery = action.payload;
    },

    clearTagSearchQuery(state) {
      state.tagQuery = '';
    },
  },
});

export const {
  startSearch,
  clearSearch,
  setTagSearchQuery,
  clearTagSearchQuery,
} = searchSlice.actions;

export default searchSlice.reducer;