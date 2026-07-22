import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Video } from '@/types/Media';

interface VideoState {
  videos: Video[];
  currentViewIndex: number;
}

const initialState: VideoState = {
  videos: [],
  currentViewIndex: -1,
};

const videoSlice = createSlice({
  name: 'videos',
  initialState,
  reducers: {
    setVideos(state, action: PayloadAction<Video[]>) {
      state.videos = action.payload;
    },

    setCurrentViewIndex(state, action: PayloadAction<number>) {
      const videoList = state.videos;
      const index = action.payload;
      if (index >= -1 && index < videoList.length) {
        state.currentViewIndex = index;
      } else {
        console.warn(
          `Invalid video index: ${index}. Valid range: -1 to ${
            videoList.length - 1
          }`,
        );
      }
    },
    closeVideoView(state) {
      state.currentViewIndex = -1;
    },

    updateVideoFavoriteStatus(state, action: PayloadAction<string>) {
      const videoId = action.payload;
      const video = state.videos.find((vid) => vid.id === videoId);
      if (video) {
        video.isFavourite = !video.isFavourite;
      }
    },

    clearVideos(state) {
      state.videos = [];
      state.currentViewIndex = -1;
    },
  },
});

export const {
  setVideos,
  setCurrentViewIndex,
  closeVideoView,
  updateVideoFavoriteStatus,
  clearVideos,
} = videoSlice.actions;

export default videoSlice.reducer;
