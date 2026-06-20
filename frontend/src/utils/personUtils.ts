import type { Cluster } from '@/types/Media';

export function getPersonName(cluster: Cluster): string {
  return cluster.cluster_name || `Person ${cluster.cluster_id.slice(-4)}`;
}

export function getPhotoCountText(count: number): string {
  return `${count} photo${count !== 1 ? 's' : ''}`;
}

/**
 * Formats selected people names into a readable title based on match mode.
 * match_any: "Person A or Person B" (any one of them)
 * match_all: "Person A & Person B" (all together)
 */
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
