import type { Cluster } from '@/types/Media';

export function getPersonName(cluster: Cluster): string {
  return cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`;
}

export function getPhotoCountText(count: number): string {
  return `${count} photo${count !== 1 ? 's' : ''}`;
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
