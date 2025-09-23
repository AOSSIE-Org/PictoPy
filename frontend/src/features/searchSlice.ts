import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

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
    setResults(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
    },
    clearSearch(state) {
      state.active = false;
      state.images = [];
      state.queryImage = undefined;
    },
  },
});

export const { startSearch, setResults, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
