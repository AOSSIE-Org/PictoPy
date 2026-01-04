import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Cluster } from '@/types/Media';

export interface FaceClustersState {
  clusters: Cluster[];
  isMergingMode: boolean;
  selectedClusterIdsForMerge: string[];
}

// Initial state
const initialState: FaceClustersState = {
  clusters: [],
  isMergingMode: false,
  selectedClusterIdsForMerge: [],
};

// Face clusters slice
const faceClustersSlice = createSlice({
  name: 'faceClusters',
  initialState,
  reducers: {
    setClusters: (state, action: PayloadAction<Cluster[]>) => {
      state.clusters = action.payload;
    },
    updateClusterName: (
      state,
      action: PayloadAction<{ clusterId: string; clusterName: string }>,
    ) => {
      const cluster = state.clusters.find(
        (c) => c.cluster_id === action.payload.clusterId,
      );
      if (cluster) {
        cluster.cluster_name = action.payload.clusterName;
      }
    },
    toggleIgnoreClusterLocal: (
      state,
      action: PayloadAction<{ clusterId: string; isIgnored: boolean }>,
    ) => {
      const cluster = state.clusters.find(
        (c) => c.cluster_id === action.payload.clusterId,
      );
      if (cluster) {
        cluster.is_ignored = action.payload.isIgnored;
      }
    },
    setMergingMode: (state, action: PayloadAction<boolean>) => {
      state.isMergingMode = action.payload;
      if (!action.payload) {
        state.selectedClusterIdsForMerge = [];
      }
    },
    toggleSelectClusterForMerge: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      if (state.selectedClusterIdsForMerge.includes(id)) {
        state.selectedClusterIdsForMerge = state.selectedClusterIdsForMerge.filter(
          (i) => i !== id,
        );
      } else {
        if (state.selectedClusterIdsForMerge.length < 2) {
          state.selectedClusterIdsForMerge.push(id);
        }
      }
    },
  },
});

export const {
  setClusters,
  updateClusterName,
  toggleIgnoreClusterLocal,
  setMergingMode,
  toggleSelectClusterForMerge,
} = faceClustersSlice.actions;
export default faceClustersSlice.reducer;
