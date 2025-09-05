/**
 * Redux Store Configuration
 * 
 * This module configures the main Redux store for the PictoPy frontend application.
 * It combines all feature slices into a single store using Redux Toolkit's
 * configureStore function for optimal performance and developer experience.
 * 
 * Store Structure:
 * - loader: Global loading states and progress indicators
 * - onboarding: User onboarding flow and initial setup
 * - images: Image data, metadata, and gallery state
 * - faceClusters: Face detection and clustering results
 * - infoDialog: Information dialogs and user notifications
 * - folders: Folder structure and organization state
 * 
 * The store uses Redux Toolkit's built-in middleware including:
 * - Redux Thunk for async actions
 * - Redux DevTools for debugging
 * - Immutability checks in development
 */

// Redux imports
import { configureStore } from '@reduxjs/toolkit';

// Feature slice imports
import loaderReducer from '@/features/loaderSlice';
import onboardingReducer from '@/features/onboardingSlice';
import imageReducer from '@/features/imageSlice';
import faceClustersReducer from '@/features/faceClustersSlice';
import infoDialogReducer from '@/features/infoDialogSlice';
import folderReducer from '@/features/folderSlice';

/**
 * Configure the main Redux store
 * 
 * Creates a Redux store with all feature reducers combined.
 * Redux Toolkit automatically includes essential middleware like
 * Redux Thunk and Redux DevTools integration.
 */
export const store = configureStore({
  reducer: {
    // Global loading states for UI feedback
    loader: loaderReducer,
    
    // User onboarding and initial setup flow
    onboarding: onboardingReducer,
    
    // Image data, metadata, and gallery management
    images: imageReducer,
    
    // Face detection, clustering, and person organization
    faceClusters: faceClustersReducer,
    
    // Information dialogs and user notifications
    infoDialog: infoDialogReducer,
    
    // Folder structure and file organization
    folders: folderReducer,
  },
});

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Root state type inferred from the store
 * 
 * This type represents the complete state shape of the application.
 * It's automatically inferred from the store configuration, ensuring
 * type safety across the entire application.
 */
export type RootState = ReturnType<typeof store.getState>;

/**
 * App dispatch type for typed dispatch actions
 * 
 * This type ensures that all dispatched actions are properly typed
 * and provides IntelliSense support for action creators.
 */
export type AppDispatch = typeof store.dispatch;
