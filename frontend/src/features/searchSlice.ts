import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@tauri-apps/api/image';

interface SearchState {
  active: boolean;
  images: Image[];
  queryImage?: string;
}

const initialState: SearchState = {
  active: false,
  images: [],
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
