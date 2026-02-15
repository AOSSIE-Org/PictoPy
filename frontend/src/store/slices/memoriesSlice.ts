/**
 * Memories Redux Slice
 *
 * Manages UI state for the Memories feature.
 * API calls are handled by Tanstack Query hooks in useMemories.tsx.
 * This slice only manages local UI state like selected memory for modal.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Memory } from '@/services/memoriesApi';

// ============================================================================
// State Interface
// ============================================================================

interface MemoriesState {
  // UI state for memory viewer modal
  selectedMemory: Memory | null;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: MemoriesState = {
  selectedMemory: null,
};

// ============================================================================
// Slice
// ============================================================================

const memoriesSlice = createSlice({
  name: 'memories',
  initialState,
  reducers: {
    /**
     * Set the selected memory for the viewer modal
     */
    setSelectedMemory: (state, action: PayloadAction<Memory | null>) => {
      state.selectedMemory = action.payload;
    },

    /**
     * Clear selected memory (close modal)
     */
    clearSelectedMemory: (state) => {
      state.selectedMemory = null;
    },

    /**
     * Reset memories UI state
     */
    resetMemories: () => {
      return initialState;
    },
  },
});

// ============================================================================
// Exports
// ============================================================================

export const { setSelectedMemory, clearSelectedMemory, resetMemories } =
  memoriesSlice.actions;

export default memoriesSlice.reducer;

// ============================================================================
// Selectors
// ============================================================================

export const selectSelectedMemory = (state: { memories: MemoriesState }) =>
  state.memories.selectedMemory;
