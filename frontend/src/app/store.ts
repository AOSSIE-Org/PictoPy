import albumReducer from '@/features/albumSlice';
import faceClustersReducer from '@/features/faceClustersSlice';
import folderReducer from '@/features/folderSlice';
import imageReducer from '@/features/imageSlice';
import infoDialogReducer from '@/features/infoDialogSlice';
import loaderReducer from '@/features/loaderSlice';
import onboardingReducer from '@/features/onboardingSlice';
import searchReducer from '@/features/searchSlice';
import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    loader: loaderReducer,
    onboarding: onboardingReducer,
    images: imageReducer,
    faceClusters: faceClustersReducer,
    infoDialog: infoDialogReducer,
    folders: folderReducer,
    search: searchReducer,
    albums: albumReducer,
  },
});
// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;
