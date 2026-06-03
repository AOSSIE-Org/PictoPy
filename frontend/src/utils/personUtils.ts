import type { Cluster } from '@/types/Media';

export function getPersonName(cluster: Cluster): string {
  return cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`;
}

export function getPhotoCountText(count: number): string {
  return `${count} photo${count !== 1 ? 's' : ''}`;
}
