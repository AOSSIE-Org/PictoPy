import { configureStore } from '@reduxjs/toolkit';
import loaderReducer from '@/features/loaderSlice';
import onboardingReducer from '@/features/onboardingSlice';
import searchReducer from '@/features/searchSlice';
import imageReducer from '@/features/imageSlice';
import faceClustersReducer from '@/features/faceClustersSlice';
import infoDialogReducer from '@/features/infoDialogSlice';
import folderReducer from '@/features/folderSlice';
import memoriesReducer from '@/features/memoriesSlice';

export const store = configureStore({
  reducer: {
    loader: loaderReducer,
    onboarding: onboardingReducer,
    images: imageReducer,
    faceClusters: faceClustersReducer,
    infoDialog: infoDialogReducer,
    folders: folderReducer,
    search: searchReducer,
    memories: memoriesReducer,
  },
});
// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;
