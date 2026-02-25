/**
 * useManualClusters
 *
 * Centralised hook for all manual-cluster operations.
 * Keeps the route components thin by containing API calls + Redux dispatch
 * in one place.
 */

import { useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/app/store';
import {
  setClusters,
  addCluster,
  updateCluster,
  removeCluster,
  setClusterDetail,
  removeImage,
} from '@/features/manualClustersSlice';
import {
  fetchAllManualClusters,
  fetchManualClusterById,
  createManualCluster,
  renameManualCluster,
  deleteManualCluster,
  assignImagesToCluster,
  removeImageFromCluster,
} from '@/api/api-functions/manual_clusters';
import {
  ManualCluster,
  ManualClusterDetail,
} from '@/types/ManualCluster';

export function useManualClusters() {
  const dispatch = useDispatch();
  const { clusters, details } = useSelector(
    (s: RootState) => s.manualClusters,
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  // ---- List ---------------------------------------------------------------

  const loadClusters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAllManualClusters();
      if (res.success && res.data) {
        dispatch(setClusters(res.data as ManualCluster[]));
      } else {
        setError(res.error ?? 'Failed to load clusters');
      }
    } catch {
      setError('Failed to load clusters');
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  // ---- Detail -------------------------------------------------------------

  const loadClusterDetail = useCallback(
    async (clusterId: string) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchManualClusterById(clusterId);
        if (res.success && res.data) {
          dispatch(setClusterDetail(res.data as ManualClusterDetail));
        } else {
          setError(res.error ?? 'Failed to load cluster');
        }
      } catch {
        setError('Failed to load cluster');
      } finally {
        setLoading(false);
      }
    },
    [dispatch],
  );

  // ---- Create -------------------------------------------------------------

  const createCluster = useCallback(
    async (name: string): Promise<ManualCluster | null> => {
      setLoading(true);
      setError(null);
      try {
        const res = await createManualCluster({ name });
        if (res.success && res.data) {
          dispatch(addCluster(res.data as ManualCluster));
          return res.data as ManualCluster;
        }
        setError(res.error ?? 'Failed to create cluster');
        return null;
      } catch {
        setError('Failed to create cluster');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [dispatch],
  );

  // ---- Rename -------------------------------------------------------------

  const renameCluster = useCallback(
    async (clusterId: string, name: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const res = await renameManualCluster(clusterId, { name });
        if (res.success && res.data) {
          dispatch(updateCluster(res.data as ManualCluster));
          return true;
        }
        setError(res.error ?? 'Failed to rename cluster');
        return false;
      } catch {
        setError('Failed to rename cluster');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [dispatch],
  );

  // ---- Delete -------------------------------------------------------------

  const deleteCluster = useCallback(
    async (clusterId: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const res = await deleteManualCluster(clusterId);
        if (res.success) {
          dispatch(removeCluster(clusterId));
          return true;
        }
        setError(res.error ?? 'Failed to delete cluster');
        return false;
      } catch {
        setError('Failed to delete cluster');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [dispatch],
  );

  // ---- Assign images ------------------------------------------------------

  const assignImages = useCallback(
    async (
      clusterId: string,
      imageIds: string[],
    ): Promise<{ assigned: number; skipped: number } | null> => {
      setLoading(true);
      setError(null);
      try {
        const res = await assignImagesToCluster(clusterId, {
          image_ids: imageIds,
        });
        if (res.success) {
          // Reload the detail to get the updated image list
          const detailRes = await fetchManualClusterById(clusterId);
          if (detailRes.success && detailRes.data) {
            dispatch(setClusterDetail(detailRes.data as ManualClusterDetail));
          }
          return {
            assigned: (res as any).assigned_count ?? 0,
            skipped: (res as any).skipped_count ?? 0,
          };
        }
        setError(res.error ?? 'Failed to assign images');
        return null;
      } catch {
        setError('Failed to assign images');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [dispatch],
  );

  // ---- Remove image -------------------------------------------------------

  const removeImageFromClusters = useCallback(
    async (clusterId: string, imageId: string): Promise<boolean> => {
      // Optimistic update
      dispatch(removeImage({ clusterId, imageId }));
      try {
        const res = await removeImageFromCluster(clusterId, imageId);
        if (!res.success) {
          // Rollback: reload detail
          const detailRes = await fetchManualClusterById(clusterId);
          if (detailRes.success && detailRes.data) {
            dispatch(setClusterDetail(detailRes.data as ManualClusterDetail));
          }
          setError(res.error ?? 'Failed to remove image');
          return false;
        }
        return true;
      } catch {
        // Rollback
        const detailRes = await fetchManualClusterById(clusterId);
        if (detailRes.success && detailRes.data) {
          dispatch(setClusterDetail(detailRes.data as ManualClusterDetail));
        }
        setError('Failed to remove image');
        return false;
      }
    },
    [dispatch],
  );

  return {
    clusters,
    details,
    loading,
    error,
    clearError,
    loadClusters,
    loadClusterDetail,
    createCluster,
    renameCluster,
    deleteCluster,
    assignImages,
    removeImageFromClusters,
  };
}
