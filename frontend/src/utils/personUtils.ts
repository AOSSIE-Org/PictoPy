import type { Cluster, Image } from '@/types/Media';
import type { FacePhoto } from '@/api/api-functions/face_clusters';

export function getPersonName(cluster: Cluster): string {
  return cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`;
}

/** Face routes leave out the gallery's bookkeeping fields; fill them in. */
export function facePhotoToImage(photo: FacePhoto): Image {
  return {
    id: photo.id,
    path: photo.path,
    thumbnailPath: photo.thumbnailPath || '',
    metadata: photo.metadata ?? undefined,
    folder_id: '',
    isTagged: true,
  };
}

export function getPhotoCountText(count: number, videoCount = 0): string {
  const photos = `${count} photo${count !== 1 ? 's' : ''}`;
  if (!videoCount) return photos;
  return `${photos} · ${videoCount} video${videoCount !== 1 ? 's' : ''}`;
}

// match_any reads "A or B", match_all reads "A and B" -- the title has to say
// which query actually ran.
export function formatPeopleTitle(
  names: string[],
  matchMode: 'match_any' | 'match_all',
): string {
  if (names.length === 0) return '';
  if (names.length === 1) return names[0];

  const last = names[names.length - 1];
  const rest = names.slice(0, -1);
  const connector = matchMode === 'match_any' ? ' or ' : ' and ';

  return rest.join(', ') + connector + last;
}
