import { RootState } from '@/app/store';
import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectImages = (state: RootState) => {
  return state.images.images;
};
export const selectViewerImages = (state: RootState) =>
  state.images.viewerImages;
export const selectCurrentViewIndex = (state: RootState) =>
  state.images.currentViewIndex;
export const selectTotalImages = (state: RootState) => state.images.totalImages;
export const selectImagesError = (state: RootState) => state.images.error;

// Memoized selectors
export const selectActiveImageList = createSelector(
  [selectImages, selectViewerImages],
  (defaultImages, viewerImages) => viewerImages ?? defaultImages,
);

export const selectCurrentImage = createSelector(
  [selectActiveImageList, selectCurrentViewIndex],
  (images, currentIndex) => {
    if (currentIndex >= 0 && currentIndex < images.length) {
      return images[currentIndex];
    }
    return null;
  },
);

export const selectIsImageViewOpen = createSelector(
  [selectCurrentViewIndex],
  (currentIndex) => currentIndex >= 0,
);

export const selectImageById = createSelector(
  [selectImages, (_state: RootState, imageId: string) => imageId],
  (images, imageId) => images.find((image) => image.id === imageId),
);

export const selectImagesByFolderId = createSelector(
  [selectImages, (_state: RootState, folderId: string) => folderId],
  (images, folderId) => images.filter((image) => image.folder_id === folderId),
);

export const selectTaggedImages = createSelector([selectImages], (images) =>
  images.filter((image) => image.isTagged),
);

export const selectUntaggedImages = createSelector([selectImages], (images) =>
  images.filter((image) => !image.isTagged),
);

export const selectImagesWithTags = createSelector([selectImages], (images) =>
  images.filter((image) => image.tags && image.tags.length > 0),
);
