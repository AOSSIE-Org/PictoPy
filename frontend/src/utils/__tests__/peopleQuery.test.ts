import { parsePeopleQuery, resolvePeopleQuery } from '../peopleQuery';
import type { Cluster } from '@/types/Media';

const cluster = (id: string, name: string): Cluster => ({
  cluster_id: id,
  cluster_name: name,
  face_count: 3,
});

const CLUSTERS: Cluster[] = [
  cluster('c1', 'Person A'),
  cluster('c2', 'Person B'),
  cluster('c3', 'Person C'),
  cluster('c4', 'Mary Jane'),
  cluster('c5', 'Alexander'),
  { cluster_id: 'abcd1234', cluster_name: '', face_count: 1 },
];

describe('parsePeopleQuery', () => {
  test('returns null for single-term queries', () => {
    expect(parsePeopleQuery('beach')).toBeNull();
    expect(parsePeopleQuery('Person A')).toBeNull();
    expect(parsePeopleQuery('   ')).toBeNull();
  });

  test('"and" splits into segments and means match_all', () => {
    expect(parsePeopleQuery('Person A and Person B')).toEqual({
      segments: ['Person A', 'Person B'],
      matchMode: 'match_all',
    });
  });

  test.each(['+', '&', ','])('"%s" also means match_all', (connector) => {
    expect(parsePeopleQuery(`Person A ${connector} Person B`)).toEqual({
      segments: ['Person A', 'Person B'],
      matchMode: 'match_all',
    });
  });

  test('a comma list keeps every name and means match_all', () => {
    expect(parsePeopleQuery('Person A, Person B, Person C')).toEqual({
      segments: ['Person A', 'Person B', 'Person C'],
      matchMode: 'match_all',
    });
  });

  test('"or" means match_any, and one "or" loosens the whole query', () => {
    expect(parsePeopleQuery('Person A or Person B')?.matchMode).toBe(
      'match_any',
    );
    expect(parsePeopleQuery('Person A and Person B or Person C')).toEqual({
      segments: ['Person A', 'Person B', 'Person C'],
      matchMode: 'match_any',
    });
  });

  test('connectors inside a name do not split it', () => {
    expect(parsePeopleQuery('Alexander and Person B')?.segments).toEqual([
      'Alexander',
      'Person B',
    ]);
    expect(parsePeopleQuery('Alexander')).toBeNull();
  });

  test('multi-word names survive, and stray whitespace is collapsed', () => {
    expect(parsePeopleQuery('  Mary  Jane   and  Person A ')?.segments).toEqual(
      ['Mary Jane', 'Person A'],
    );
  });

  test('a trailing connector does not produce an empty segment', () => {
    expect(parsePeopleQuery('Person A, Person B,')?.segments).toEqual([
      'Person A',
      'Person B',
    ]);
  });
});

describe('resolvePeopleQuery', () => {
  test('resolves names to clusters, case-insensitively', () => {
    const result = resolvePeopleQuery('person a AND Person B', CLUSTERS);
    expect(result?.matched.map((c) => c.cluster_id)).toEqual(['c1', 'c2']);
    expect(result?.unmatched).toEqual([]);
    expect(result?.matchMode).toBe('match_all');
  });

  test('keeps the known names and reports the unknown ones', () => {
    const result = resolvePeopleQuery(
      'Person A and Zed and Person C',
      CLUSTERS,
    );
    expect(result?.matched.map((c) => c.cluster_id)).toEqual(['c1', 'c3']);
    expect(result?.unmatched).toEqual(['Zed']);
  });

  test('returns null when fewer than two people resolve', () => {
    expect(resolvePeopleQuery('Person A and Zed', CLUSTERS)).toBeNull();
    expect(resolvePeopleQuery('sunset and beach', CLUSTERS)).toBeNull();
    expect(resolvePeopleQuery('Person A and Person B', [])).toBeNull();
  });

  test('a repeated name counts once, so it is not a people query', () => {
    expect(resolvePeopleQuery('Person A and person a', CLUSTERS)).toBeNull();
  });

  test('the generated label of an unnamed cluster is matchable', () => {
    const result = resolvePeopleQuery('Person 1234 and Person A', CLUSTERS);
    expect(result?.matched.map((c) => c.cluster_id)).toEqual([
      'abcd1234',
      'c1',
    ]);
  });
});
