import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Cluster } from '@/types/Media';

export interface FaceClustersState {
  clusters: Cluster[];
}

// Initial state
const initialState: FaceClustersState = {
  clusters: [],
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
  },
});

export const { setClusters, updateClusterName } = faceClustersSlice.actions;
export default faceClustersSlice.reducer;
