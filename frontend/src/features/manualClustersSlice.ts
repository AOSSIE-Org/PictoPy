import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  ManualCluster,
  ManualClusterDetail,
  ManualClusterImage,
} from '@/types/ManualCluster';

export interface ManualClustersState {
  clusters: ManualCluster[];
  /** Fully-loaded detail keyed by cluster_id */
  details: Record<string, ManualClusterDetail>;
}

const initialState: ManualClustersState = {
  clusters: [],
  details: {},
};

const manualClustersSlice = createSlice({
  name: 'manualClusters',
  initialState,
  reducers: {
    // --- List ---
    setClusters(state, action: PayloadAction<ManualCluster[]>) {
      state.clusters = action.payload;
    },
    addCluster(state, action: PayloadAction<ManualCluster>) {
      state.clusters.unshift(action.payload);
    },
    updateCluster(state, action: PayloadAction<ManualCluster>) {
      const idx = state.clusters.findIndex(
        (c) => c.cluster_id === action.payload.cluster_id,
      );
      if (idx !== -1) state.clusters[idx] = action.payload;
      // Also update cached detail if present
      if (state.details[action.payload.cluster_id]) {
        state.details[action.payload.cluster_id].cluster = action.payload;
      }
    },
    removeCluster(state, action: PayloadAction<string>) {
      state.clusters = state.clusters.filter(
        (c) => c.cluster_id !== action.payload,
      );
      delete state.details[action.payload];
    },

    // --- Detail ---
    setClusterDetail(state, action: PayloadAction<ManualClusterDetail>) {
      state.details[action.payload.cluster.cluster_id] = action.payload;
    },
    appendImages(
      state,
      action: PayloadAction<{ clusterId: string; images: ManualClusterImage[] }>,
    ) {
      const detail = state.details[action.payload.clusterId];
      if (detail) {
        // Deduplicate by id
        const existingIds = new Set(detail.images.map((i) => i.id));
        const newImages = action.payload.images.filter(
          (i) => !existingIds.has(i.id),
        );
        detail.images.push(...newImages);
        detail.image_count = detail.images.length;
        // Sync count on the summary list too
        const summ = state.clusters.find(
          (c) => c.cluster_id === action.payload.clusterId,
        );
        if (summ) summ.image_count = detail.image_count;
      }
    },
    removeImage(
      state,
      action: PayloadAction<{ clusterId: string; imageId: string }>,
    ) {
      const detail = state.details[action.payload.clusterId];
      if (detail) {
        detail.images = detail.images.filter(
          (i) => i.id !== action.payload.imageId,
        );
        detail.image_count = detail.images.length;
        const summ = state.clusters.find(
          (c) => c.cluster_id === action.payload.clusterId,
        );
        if (summ) summ.image_count = detail.image_count;
      }
    },
  },
});

export const {
  setClusters,
  addCluster,
  updateCluster,
  removeCluster,
  setClusterDetail,
  appendImages,
  removeImage,
} = manualClustersSlice.actions;

export default manualClustersSlice.reducer;
