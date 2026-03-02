import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchState {
  active: boolean;
  queryImage?: string;
  queryText?: string;
  textSearchActive: boolean;
}

const initialState: SearchState = {
  active: false,
  queryImage: undefined,
  queryText: undefined,
  textSearchActive: false,
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
    startTextSearch(state, action: PayloadAction<string>) {
      state.textSearchActive = true;
      state.queryText = action.payload;
    },
    clearTextSearch(state) {
      state.textSearchActive = false;
      state.queryText = undefined;
    },
  },
});

export const { startSearch, clearSearch, startTextSearch, clearTextSearch } =
  searchSlice.actions;
export default searchSlice.reducer;
