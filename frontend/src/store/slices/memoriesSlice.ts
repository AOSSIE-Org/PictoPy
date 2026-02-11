/**
 * Memories Redux Slice
 *
 * Manages state for the Memories feature including:
 * - All memories (generated from all photos)
 * - Recent memories (last 30 days)
 * - Year memories (current year)
 * - On This Day images
 * - Selected memory for viewer modal
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  generateMemories,
  getTimeline,
  getOnThisDay,
  Memory,
  MemoryImage,
  ApiError,
} from '@/services/memoriesApi';

// ============================================================================
// State Interface
// ============================================================================

interface MemoriesState {
  // Memory collections
  allMemories: Memory[];
  recentMemories: Memory[];
  yearMemories: Memory[];
  onThisDayImages: MemoryImage[];
  onThisDayMeta: {
    today: string;
    years: number[];
  } | null;

  // Loading states for each section
  loading: {
    all: boolean;
    recent: boolean;
    year: boolean;
    onThisDay: boolean;
  };

  // Error states
  error: {
    all: string | null;
    recent: string | null;
    year: string | null;
    onThisDay: string | null;
  };

  // Metadata
  lastFetched: number | null;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: MemoriesState = {
  allMemories: [],
  recentMemories: [],
  yearMemories: [],
  onThisDayImages: [],
  onThisDayMeta: null,
  loading: {
    all: false,
    recent: false,
    year: false,
    onThisDay: false,
  },
  error: {
    all: null,
    recent: null,
    year: null,
    onThisDay: null,
  },
  lastFetched: null,
};

// ============================================================================
// Async Thunks
// ============================================================================

/**
 * Fetch all memories from photos with location data
 */
export const fetchAllMemories = createAsyncThunk<
  Memory[],
  void,
  { rejectValue: string }
>('memories/fetchAll', async (_, { rejectWithValue }) => {
  try {
    const response = await generateMemories();
    return response.memories;
  } catch (error) {
    const apiError = error as ApiError;
    return rejectWithValue(apiError.message);
  }
});

/**
 * Fetch recent memories (last 30 days)
 */
export const fetchRecentMemories = createAsyncThunk<
  Memory[],
  number,
  { rejectValue: string }
>('memories/fetchRecent', async (days = 30, { rejectWithValue }) => {
  try {
    const response = await getTimeline(days);
    return response.memories;
  } catch (error) {
    const apiError = error as ApiError;
    return rejectWithValue(apiError.message);
  }
});

/**
 * Fetch memories from current year
 */
export const fetchYearMemories = createAsyncThunk<
  Memory[],
  number,
  { rejectValue: string }
>('memories/fetchYear', async (days = 365, { rejectWithValue }) => {
  try {
    const response = await getTimeline(days);
    return response.memories;
  } catch (error) {
    const apiError = error as ApiError;
    return rejectWithValue(apiError.message);
  }
});

/**
 * Fetch "On This Day" images
 */
export const fetchOnThisDay = createAsyncThunk<
  { images: MemoryImage[]; today: string; years: number[] },
  void,
  { rejectValue: string }
>('memories/fetchOnThisDay', async (_, { rejectWithValue }) => {
  try {
    const response = await getOnThisDay();
    return {
      images: response.images,
      today: response.today,
      years: response.years,
    };
  } catch (error) {
    const apiError = error as ApiError;
    return rejectWithValue(apiError.message);
  }
});

/**
 * Fetch all memories data at once (parallel requests)
 */
export const fetchAllMemoriesData = createAsyncThunk<
  void,
  void,
  { rejectValue: string }
>('memories/fetchAllData', async (_, { dispatch, rejectWithValue }) => {
  try {
    await Promise.all([
      dispatch(fetchOnThisDay()),
      dispatch(fetchRecentMemories(30)),
      dispatch(fetchYearMemories(365)),
      dispatch(fetchAllMemories()),
    ]);
  } catch (error) {
    const apiError = error as ApiError;
    return rejectWithValue(apiError.message);
  }
});

// ============================================================================
// Slice
// ============================================================================

const memoriesSlice = createSlice({
  name: 'memories',
  initialState,
  reducers: {
    /**
     * Toggle favorite status of an image across all memories
     */
    toggleImageFavorite: (state, action: PayloadAction<string>) => {
      const imageId = action.payload;

      // Helper function to update image in a memory array
      const updateMemoriesArray = (memories: Memory[]) => {
        memories.forEach((memory) => {
          memory.images.forEach((image) => {
            if (image.id === imageId) {
              image.isFavourite = !image.isFavourite;
            }
          });
        });
      };

      // Update across all memory collections
      updateMemoriesArray(state.allMemories);
      updateMemoriesArray(state.recentMemories);
      updateMemoriesArray(state.yearMemories);

      // Update onThisDay images
      state.onThisDayImages.forEach((image) => {
        if (image.id === imageId) {
          image.isFavourite = !image.isFavourite;
        }
      });
    },

    /**
     * Clear all errors
     */
    clearErrors: (state) => {
      state.error = {
        all: null,
        recent: null,
        year: null,
        onThisDay: null,
      };
    },

    /**
     * Reset memories state
     */
    resetMemories: () => {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    // ========================================================================
    // Fetch All Memories
    // ========================================================================
    builder
      .addCase(fetchAllMemories.pending, (state) => {
        state.loading.all = true;
        state.error.all = null;
      })
      .addCase(fetchAllMemories.fulfilled, (state, action) => {
        state.loading.all = false;
        state.allMemories = action.payload;
        state.lastFetched = Date.now();
      })
      .addCase(fetchAllMemories.rejected, (state, action) => {
        state.loading.all = false;
        state.error.all = action.payload || 'Failed to fetch memories';
      });

    // ========================================================================
    // Fetch Recent Memories
    // ========================================================================
    builder
      .addCase(fetchRecentMemories.pending, (state) => {
        state.loading.recent = true;
        state.error.recent = null;
      })
      .addCase(fetchRecentMemories.fulfilled, (state, action) => {
        state.loading.recent = false;
        state.recentMemories = action.payload;
      })
      .addCase(fetchRecentMemories.rejected, (state, action) => {
        state.loading.recent = false;
        state.error.recent =
          action.payload || 'Failed to fetch recent memories';
      });

    // ========================================================================
    // Fetch Year Memories
    // ========================================================================
    builder
      .addCase(fetchYearMemories.pending, (state) => {
        state.loading.year = true;
        state.error.year = null;
      })
      .addCase(fetchYearMemories.fulfilled, (state, action) => {
        state.loading.year = false;
        state.yearMemories = action.payload;
      })
      .addCase(fetchYearMemories.rejected, (state, action) => {
        state.loading.year = false;
        state.error.year = action.payload || 'Failed to fetch year memories';
      });

    // ========================================================================
    // Fetch On This Day
    // ========================================================================
    builder
      .addCase(fetchOnThisDay.pending, (state) => {
        state.loading.onThisDay = true;
        state.error.onThisDay = null;
      })
      .addCase(fetchOnThisDay.fulfilled, (state, action) => {
        state.loading.onThisDay = false;
        state.onThisDayImages = action.payload.images;
        state.onThisDayMeta = {
          today: action.payload.today,
          years: action.payload.years,
        };
      })
      .addCase(fetchOnThisDay.rejected, (state, action) => {
        state.loading.onThisDay = false;
        state.error.onThisDay = action.payload || 'Failed to fetch On This Day';
      });
  },
});

// ============================================================================
// Exports
// ============================================================================

export const {
  toggleImageFavorite,
  clearErrors,
  resetMemories,
} = memoriesSlice.actions;

export default memoriesSlice.reducer;

// ============================================================================
// Selectors
// ============================================================================

export const selectAllMemories = (state: { memories: MemoriesState }) =>
  state.memories.allMemories;
export const selectRecentMemories = (state: { memories: MemoriesState }) =>
  state.memories.recentMemories;
export const selectYearMemories = (state: { memories: MemoriesState }) =>
  state.memories.yearMemories;
export const selectOnThisDayImages = (state: { memories: MemoriesState }) =>
  state.memories.onThisDayImages;
export const selectOnThisDayMeta = (state: { memories: MemoriesState }) =>
  state.memories.onThisDayMeta;
export const selectMemoriesLoading = (state: { memories: MemoriesState }) =>
  state.memories.loading;
export const selectMemoriesError = (state: { memories: MemoriesState }) =>
  state.memories.error;
export const selectLastFetched = (state: { memories: MemoriesState }) =>
  state.memories.lastFetched;

/**
 * Select total memory count across all sections
 */
export const selectTotalMemoryCount = (state: { memories: MemoriesState }) => {
  return state.memories.allMemories.length;
};

/**
 * Check if any section is loading
 */
export const selectIsAnyLoading = (state: { memories: MemoriesState }) => {
  const { loading } = state.memories;
  return loading.all || loading.recent || loading.year || loading.onThisDay;
};

/**
 * Check if there are any errors
 */
export const selectHasAnyError = (state: { memories: MemoriesState }) => {
  const { error } = state.memories;
  return !!(error.all || error.recent || error.year || error.onThisDay);
};
