export interface ManualCluster {
  cluster_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  is_auto_generated: boolean;
  image_count: number;
}

export interface ManualClusterImage {
  id: string;
  path: string;
  thumbnailPath?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface ManualClusterDetail {
  cluster: ManualCluster;
  images: ManualClusterImage[];
  image_count: number;
}

// Request types
export interface CreateClusterPayload {
  name: string;
}

export interface RenameClusterPayload {
  name: string;
}

export interface AssignImagesPayload {
  image_ids: string[];
}
