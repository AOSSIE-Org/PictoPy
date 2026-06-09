import { configureStore, combineReducers } from '@reduxjs/toolkit';
import loaderReducer from '@/features/loaderSlice';
import onboardingReducer from '@/features/onboardingSlice';
import searchReducer from '@/features/searchSlice';
import imageReducer from '@/features/imageSlice';
import faceClustersReducer from '@/features/faceClustersSlice';
import infoDialogReducer from '@/features/infoDialogSlice';
import globalAlertReducer from '@/features/globalAlertSlice';
import folderReducer from '@/features/folderSlice';
import memoriesReducer from '@/features/memoriesSlice';

export const rootReducer = combineReducers({
  loader: loaderReducer,
  onboarding: onboardingReducer,
  images: imageReducer,
  faceClusters: faceClustersReducer,
  infoDialog: infoDialogReducer,
  globalAlert: globalAlertReducer,
  folders: folderReducer,
  search: searchReducer,
  memories: memoriesReducer,
});

export const store = configureStore({
  reducer: rootReducer,
});
// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {loader: LoaderState, onboarding: OnboardingState, images: ImageState, ...}
export type AppDispatch = typeof store.dispatch;
