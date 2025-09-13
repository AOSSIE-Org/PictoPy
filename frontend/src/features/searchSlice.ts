import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Image } from '@/types/Media';

interface SearchState {
  active: boolean;
  images: Image[];
  loading: boolean;
  queryImage?: string;
}

const initialState: SearchState = {
  active: false,
  images: [],
  loading: false,
  queryImage: undefined,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    startSearch(state, action: PayloadAction<string>) {
      state.active = true;
      state.loading = true;
      state.queryImage = action.payload;
    },
    setResults(state, action: PayloadAction<Image[]>) {
      state.images = action.payload;
      state.loading = false;
    },
    clearSearch(state) {
      state.active = false;
      state.images = [];
      state.loading = false;
      state.queryImage = undefined;
    },
  },
});

export const { startSearch, setResults, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
