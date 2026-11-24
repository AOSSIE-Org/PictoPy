import reducer, {
  clearFaceSelection,
  clearSearch,
  setFaceSelection,
  startSearch,
} from '../searchSlice';
import { MAX_SELECTED_FACES } from '@/utils/faceSearch';

const empty = reducer(undefined, { type: 'init' });

describe('searchSlice', () => {
  test('starts with nothing selected', () => {
    expect(empty).toEqual({
      queryImage: undefined,
      faceSelection: undefined,
    });
  });

  test('stores the picked faces and mode', () => {
    const state = reducer(
      empty,
      setFaceSelection({ indices: [0, 2], matchMode: 'match_all' }),
    );
    expect(state.faceSelection).toEqual({
      indices: [0, 2],
      matchMode: 'match_all',
    });
  });

  test('forces match_any for a single face', () => {
    const state = reducer(
      empty,
      setFaceSelection({ indices: [1], matchMode: 'match_all' }),
    );
    expect(state.faceSelection?.matchMode).toBe('match_any');
  });

  test('drops duplicates, negatives and non-integers', () => {
    const state = reducer(
      empty,
      setFaceSelection({ indices: [1, 1, -1, 0.5, 3], matchMode: 'match_any' }),
    );
    expect(state.faceSelection?.indices).toEqual([1, 3]);
  });

  test('keeps at most the backend limit', () => {
    const indices = Array.from({ length: MAX_SELECTED_FACES + 3 }, (_, i) => i);
    const state = reducer(
      empty,
      setFaceSelection({ indices, matchMode: 'match_any' }),
    );
    expect(state.faceSelection?.indices).toHaveLength(MAX_SELECTED_FACES);
  });

  test('ignores a selection with no usable faces', () => {
    const picked = reducer(
      empty,
      setFaceSelection({ indices: [0], matchMode: 'match_any' }),
    );
    const state = reducer(
      picked,
      setFaceSelection({ indices: [], matchMode: 'match_any' }),
    );
    expect(state.faceSelection?.indices).toEqual([0]);
  });

  test('a new query photo forgets the old selection', () => {
    const picked = reducer(
      empty,
      setFaceSelection({ indices: [0], matchMode: 'match_any' }),
    );
    const state = reducer(picked, startSearch('/photos/new.jpg'));
    expect(state.queryImage).toBe('/photos/new.jpg');
    expect(state.faceSelection).toBeUndefined();
  });

  test('clearSearch clears the photo and the selection', () => {
    const picked = reducer(
      reducer(empty, startSearch('/photos/a.jpg')),
      setFaceSelection({ indices: [0], matchMode: 'match_any' }),
    );
    expect(reducer(picked, clearSearch())).toEqual(empty);
  });

  test('clearFaceSelection keeps the photo', () => {
    const picked = reducer(
      reducer(empty, startSearch('/photos/a.jpg')),
      setFaceSelection({ indices: [0], matchMode: 'match_any' }),
    );
    const state = reducer(picked, clearFaceSelection());
    expect(state.queryImage).toBe('/photos/a.jpg');
    expect(state.faceSelection).toBeUndefined();
  });
});
