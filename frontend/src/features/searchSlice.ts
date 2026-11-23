import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchState {
  queryImage?: string;
}

const initialState: SearchState = {
  queryImage: undefined,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startSearch(state, action: PayloadAction<string>) {
      state.queryImage = action.payload;
    },
    clearSearch(state) {
      state.queryImage = undefined;
    },
  },
});

export const { startSearch, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
