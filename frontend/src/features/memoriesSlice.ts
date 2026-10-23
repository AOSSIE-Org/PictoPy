/**
 * Memories Redux slice.
 *
 * Holds story-viewer UI state only. Memory data itself lives in React Query,
 * matching how the rest of the app splits server and UI state.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '@/app/store';

export const DEFAULT_SLIDE_DURATION_MS = 5000;

interface MemoriesState {
  /** Memory currently open in the story viewer, or null when closed. */
  activeMemoryId: string | null;
  slideIndex: number;
  isPlaying: boolean;
  /** The viewer ships muted; audio is opt-in. */
  isMuted: boolean;
  slideDurationMs: number;
}

const initialState: MemoriesState = {
  activeMemoryId: null,
  slideIndex: 0,
  isPlaying: true,
  isMuted: true,
  slideDurationMs: DEFAULT_SLIDE_DURATION_MS,
};

const memoriesSlice = createSlice({
  name: 'memories',
  initialState,
  reducers: {
    openMemory: (state, action: PayloadAction<string>) => {
      state.activeMemoryId = action.payload;
      state.slideIndex = 0;
      state.isPlaying = true;
    },
    closeMemory: (state) => {
      state.activeMemoryId = null;
      state.slideIndex = 0;
    },
    setSlideIndex: (state, action: PayloadAction<number>) => {
      state.slideIndex = Math.max(0, action.payload);
    },
    setPlaying: (state, action: PayloadAction<boolean>) => {
      state.isPlaying = action.payload;
    },
    togglePlaying: (state) => {
      state.isPlaying = !state.isPlaying;
    },
    setMuted: (state, action: PayloadAction<boolean>) => {
      state.isMuted = action.payload;
    },
    toggleMuted: (state) => {
      state.isMuted = !state.isMuted;
    },
    setSlideDuration: (state, action: PayloadAction<number>) => {
      state.slideDurationMs = Math.max(1000, action.payload);
    },
    resetMemories: () => initialState,
  },
});

export const {
  openMemory,
  closeMemory,
  setSlideIndex,
  setPlaying,
  togglePlaying,
  setMuted,
  toggleMuted,
  setSlideDuration,
  resetMemories,
} = memoriesSlice.actions;

export default memoriesSlice.reducer;

export const selectActiveMemoryId = (state: RootState) =>
  state.memories.activeMemoryId;
export const selectSlideIndex = (state: RootState) => state.memories.slideIndex;
export const selectIsPlaying = (state: RootState) => state.memories.isPlaying;
export const selectIsMuted = (state: RootState) => state.memories.isMuted;
export const selectSlideDurationMs = (state: RootState) =>
  state.memories.slideDurationMs;
