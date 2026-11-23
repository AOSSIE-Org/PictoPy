import type { PropsWithChildren } from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { act, renderHook } from '@testing-library/react';
import { rootReducer } from '@/app/store';
import { useGalleryView } from '../useGalleryView';

const STORAGE_KEY = 'pictopy-gallery-view';
const SECTIONS = [
  'AI Tagging',
  'Home',
  'Favourites',
  'Videos',
  'Albums',
  'Memories',
];

function createGalleryViewHook() {
  const store = configureStore({ reducer: rootReducer });
  const wrapper = ({ children }: PropsWithChildren) => (
    <Provider store={store}>{children}</Provider>
  );
  return { ...renderHook(() => useGalleryView(), { wrapper }), store };
}

describe('useGalleryView', () => {
  beforeEach(() => localStorage.clear());

  it('defaults to Medium and safely handles old or invalid saved values', () => {
    expect(createGalleryViewHook().result.current[0]).toBe('medium');

    localStorage.setItem(STORAGE_KEY, '{bad json');
    expect(createGalleryViewHook().result.current[0]).toBe('medium');

    localStorage.setItem(STORAGE_KEY, JSON.stringify({ layout: 'river' }));
    expect(createGalleryViewHook().result.current[0]).toBe('medium');

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ layout: 'square', size: 'large' }),
    );
    expect(createGalleryViewHook().result.current[0]).toBe('large');
  });

  it('migrates density preferences and persists the selected size', () => {
    localStorage.setItem('pictopy-gallery-density', 'compact');
    const { result } = createGalleryViewHook();
    expect(result.current[0]).toBe('small');

    act(() => result.current[1]('large'));
    expect(result.current[0]).toBe('large');
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null')).toEqual({
      size: 'large',
    });
  });

  it.each(SECTIONS)(
    'synchronizes a change from %s to every gallery section',
    (source) => {
      const store = configureStore({ reducer: rootReducer });
      const wrapper = ({ children }: PropsWithChildren) => (
        <Provider store={store}>{children}</Provider>
      );
      const consumers = SECTIONS.map(() =>
        renderHook(() => useGalleryView(), { wrapper }),
      );

      const sourceIndex = SECTIONS.indexOf(source);
      act(() => consumers[sourceIndex].result.current[1]('large'));
      consumers.forEach(({ result }) => {
        expect(result.current[0]).toBe('large');
      });
      consumers.forEach(({ unmount }) => unmount());
    },
  );

  it('restores the saved size after navigation and application restart', () => {
    const firstPage = createGalleryViewHook();
    act(() => firstPage.result.current[1]('small'));
    firstPage.unmount();

    const nextPage = createGalleryViewHook();
    expect(nextPage.result.current[0]).toBe('small');
  });

  it('does not modify sorting preferences', () => {
    const sortKey = 'pictopy-ai-tagging-sort';
    localStorage.setItem(sortKey, 'oldest');
    const { result } = createGalleryViewHook();

    act(() => result.current[1]('large'));

    expect(localStorage.getItem(sortKey)).toBe('oldest');
  });
});
