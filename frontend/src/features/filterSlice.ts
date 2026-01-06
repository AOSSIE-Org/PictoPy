import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface FilterState {
  tags: string[];
  isFavourite: boolean | null; // null = all, true = favourites only, false = non-favourites
  isTagged: boolean | null;
  dateRange: {
    start: string | null;
    end: string | null;
  };
  fileSize: {
    min: number | null;
    max: number | null;
  };
  fileTypes: string[];
  location: {
    enabled: boolean;
    latitude?: number;
    longitude?: number;
    radius?: number; // in km
  };
  active: boolean;
}

const initialState: FilterState = {
  tags: [],
  isFavourite: null,
  isTagged: null,
  dateRange: {
    start: null,
    end: null,
  },
  fileSize: {
    min: null,
    max: null,
  },
  fileTypes: [],
  location: {
    enabled: false,
  },
  active: false,
};

// Helper function to calculate if any filter is active
const calculateActiveState = (state: FilterState): boolean => {
  return (
    state.tags.length > 0 ||
    state.isFavourite !== null ||
    state.isTagged !== null ||
    state.dateRange.start !== null ||
    state.dateRange.end !== null ||
    state.fileSize.min !== null ||
    state.fileSize.max !== null ||
    state.fileTypes.length > 0 ||
    state.location.enabled
  );
};

const filterSlice = createSlice({
  name: 'filters',
  initialState,
  reducers: {
    setTags(state, action: PayloadAction<string[]>) {
      state.tags = action.payload;
      state.active = calculateActiveState(state);
    },
    setIsFavourite(state, action: PayloadAction<boolean | null>) {
      state.isFavourite = action.payload;
      state.active = calculateActiveState(state);
    },
    setIsTagged(state, action: PayloadAction<boolean | null>) {
      state.isTagged = action.payload;
      state.active = calculateActiveState(state);
    },
    setDateRange(state, action: PayloadAction<{ start: string | null; end: string | null }>) {
      state.dateRange = action.payload;
      state.active = calculateActiveState(state);
    },
    setFileSize(state, action: PayloadAction<{ min: number | null; max: number | null }>) {
      state.fileSize = action.payload;
      // Only set active if at least one file size value is provided
      state.active = calculateActiveState(state);
    },
    setFileTypes(state, action: PayloadAction<string[]>) {
      state.fileTypes = action.payload;
      // Only set active if file types array has items
      state.active = calculateActiveState(state);
    },
    setLocation(state, action: PayloadAction<FilterState['location']>) {
      state.location = action.payload;
      state.active = calculateActiveState(state);
    },
    clearFilters(state) {
      return initialState;
    },
    resetFilters(state) {
      state.active = false;
      state.tags = [];
      state.isFavourite = null;
      state.isTagged = null;
      state.dateRange = { start: null, end: null };
      state.fileSize = { min: null, max: null };
      state.fileTypes = [];
      state.location = { enabled: false };
    },
  },
});

export const {
  setTags,
  setIsFavourite,
  setIsTagged,
  setDateRange,
  setFileSize,
  setFileTypes,
  setLocation,
  clearFilters,
  resetFilters,
} = filterSlice.actions;

export default filterSlice.reducer;