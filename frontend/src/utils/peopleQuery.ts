import type { Cluster } from '@/types/Media';
import { getPersonName } from '@/utils/personUtils';

export type MatchMode = 'match_any' | 'match_all';

export interface ParsedPeopleQuery {
  /** Raw name fragments, in the order they were typed. */
  segments: string[];
  matchMode: MatchMode;
}

export interface ResolvedPeopleQuery {
  matched: Cluster[];
  /** Fragments that matched no labelled cluster. */
  unmatched: string[];
  matchMode: MatchMode;
}

// Capturing group so String.split keeps the connectors: even indices are name
// fragments, odd indices are the connector that preceded the next one.
// \b keeps "Alexander" and "Randy" from being split on their inner and/or.
const CONNECTOR_PATTERN = /\s*(,|\+|&|\band\b|\bor\b)\s*/i;

const normalize = (value: string) => value.trim().replace(/\s+/g, ' ');

/** Null for anything that is not a multi-name query. */
export function parsePeopleQuery(query: string): ParsedPeopleQuery | null {
  const normalized = normalize(query);
  if (!normalized) return null;

  const parts = normalized.split(CONNECTOR_PATTERN);
  if (parts.length < 3) return null;

  const segments: string[] = [];
  let hasOr = false;

  parts.forEach((part, index) => {
    const value = normalize(part ?? '');
    if (index % 2 === 0) {
      if (value) segments.push(value);
    } else if (value.toLowerCase() === 'or') {
      hasOr = true;
    }
  });

  if (segments.length < 2) return null;

  // A single "or" anywhere loosens the whole query; and/comma/+/& mean "all".
  return { segments, matchMode: hasOr ? 'match_any' : 'match_all' };
}

function findClusterByName(
  clusters: Cluster[],
  name: string,
): Cluster | undefined {
  const target = name.toLowerCase();
  return clusters.find((cluster) => {
    const label = cluster.cluster_name?.trim().toLowerCase();
    // Fall back to the displayed label so "Person 1a2b" is typeable too.
    return label === target || getPersonName(cluster).toLowerCase() === target;
  });
}

// Null unless at least two distinct people resolve, so single-name and ordinary
// text queries fall through to tag/semantic search untouched.
export function resolvePeopleQuery(
  query: string,
  clusters: Cluster[],
): ResolvedPeopleQuery | null {
  const parsed = parsePeopleQuery(query);
  if (!parsed || clusters.length === 0) return null;

  const matched: Cluster[] = [];
  const unmatched: string[] = [];
  const seen = new Set<string>();

  for (const segment of parsed.segments) {
    const cluster = findClusterByName(clusters, segment);
    if (!cluster) {
      unmatched.push(segment);
    } else if (!seen.has(cluster.cluster_id)) {
      seen.add(cluster.cluster_id);
      matched.push(cluster);
    }
  }

  if (matched.length < 2) return null;

  return { matched, unmatched, matchMode: parsed.matchMode };
}
