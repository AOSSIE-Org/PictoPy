import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SearchState {
  active: boolean;
  queryImage?: string;
}

const initialState: SearchState = {
  active: false,
  queryImage: undefined,
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
  },
});

export const { startSearch, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
