import reducer, {
  DEFAULT_SLIDE_DURATION_MS,
  closeMemory,
  openMemory,
  resetMemories,
  setMuted,
  setPlaying,
  setSlideDuration,
  setSlideIndex,
  toggleMuted,
  togglePlaying,
} from '../memoriesSlice';

const initialState = reducer(undefined, { type: '@@INIT' });

describe('memoriesSlice', () => {
  describe('initial state', () => {
    it('starts closed, playing, and muted', () => {
      expect(initialState).toEqual({
        activeMemoryId: null,
        slideIndex: 0,
        isPlaying: true,
        isMuted: true,
        slideDurationMs: DEFAULT_SLIDE_DURATION_MS,
      });
    });

    it('defaults to five seconds per slide', () => {
      expect(DEFAULT_SLIDE_DURATION_MS).toBe(5000);
    });
  });

  describe('openMemory', () => {
    it('selects the memory and starts from the first slide', () => {
      const state = reducer(
        { ...initialState, slideIndex: 4, isPlaying: false },
        openMemory('mem-1'),
      );

      expect(state.activeMemoryId).toBe('mem-1');
      expect(state.slideIndex).toBe(0);
      expect(state.isPlaying).toBe(true);
    });

    it('rewinds when switching to a different memory', () => {
      let state = reducer(initialState, openMemory('mem-1'));
      state = reducer(state, setSlideIndex(3));
      state = reducer(state, openMemory('mem-2'));

      expect(state.activeMemoryId).toBe('mem-2');
      expect(state.slideIndex).toBe(0);
    });

    it('preserves the mute preference across memories', () => {
      let state = reducer(initialState, setMuted(false));
      state = reducer(state, openMemory('mem-1'));

      expect(state.isMuted).toBe(false);
    });
  });

  describe('closeMemory', () => {
    it('clears the selection and the slide position', () => {
      let state = reducer(initialState, openMemory('mem-1'));
      state = reducer(state, setSlideIndex(2));
      state = reducer(state, closeMemory());

      expect(state.activeMemoryId).toBeNull();
      expect(state.slideIndex).toBe(0);
    });
  });

  describe('setSlideIndex', () => {
    it.each([
      [3, 3],
      [0, 0],
      [-1, 0],
      [-99, 0],
    ])('clamps %p to %p', (input, expected) => {
      expect(reducer(initialState, setSlideIndex(input)).slideIndex).toBe(
        expected,
      );
    });
  });

  describe('playback and audio toggles', () => {
    it('toggles playing', () => {
      const paused = reducer(initialState, togglePlaying());
      expect(paused.isPlaying).toBe(false);
      expect(reducer(paused, togglePlaying()).isPlaying).toBe(true);
    });

    it('toggles muting', () => {
      const unmuted = reducer(initialState, toggleMuted());
      expect(unmuted.isMuted).toBe(false);
      expect(reducer(unmuted, toggleMuted()).isMuted).toBe(true);
    });

    it.each([true, false])('sets playing to %p explicitly', (value) => {
      expect(reducer(initialState, setPlaying(value)).isPlaying).toBe(value);
    });
  });

  describe('setSlideDuration', () => {
    it.each([
      [8000, 8000],
      [1000, 1000],
      // A sub-second slide would make the story unreadable.
      [500, 1000],
      [0, 1000],
      [-1000, 1000],
    ])('clamps %p ms to %p ms', (input, expected) => {
      expect(
        reducer(initialState, setSlideDuration(input)).slideDurationMs,
      ).toBe(expected);
    });
  });

  describe('resetMemories', () => {
    it('returns to the initial state', () => {
      let state = reducer(initialState, openMemory('mem-1'));
      state = reducer(state, setSlideIndex(5));
      state = reducer(state, setMuted(false));

      expect(reducer(state, resetMemories())).toEqual(initialState);
    });
  });
});
