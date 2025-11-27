import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type SearchType = 'text' | 'face' | null;

interface SearchState {
  active: boolean;
  type: SearchType;
  query?: string; // Text search query
  queryImage?: string; // Face search image path
}

const initialState: SearchState = {
  active: false,
  type: null,
  query: undefined,
  queryImage: undefined,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startTextSearch(state, action: PayloadAction<string>) {
      state.active = true;
      state.type = 'text';
      state.query = action.payload;
      state.queryImage = undefined;
    },
    startFaceSearch(state, action: PayloadAction<string>) {
      state.active = true;
      state.type = 'face';
      state.queryImage = action.payload;
      state.query = undefined;
    },
    clearSearch(state) {
      state.active = false;
      state.type = null;
      state.query = undefined;
      state.queryImage = undefined;
    },
  },
});

export const { startTextSearch, startFaceSearch, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;