import { render, screen, fireEvent, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from '@/app/store';
import { setVideos, setCurrentViewIndex } from '@/features/videoSlice';
import { VideoPlayerOverlay } from '../VideoPlayerOverlay';
import { Video } from '@/types/Media';

const mockToggleFavourite = jest.fn();
jest.mock('@/hooks/useToggleVideoFav', () => ({
  useToggleVideoFav: () => ({
    toggleFavourite: mockToggleFavourite,
    toggleFavouritePending: false,
  }),
}));

const mockRevealItemInDir = jest.fn().mockResolvedValue(undefined);
jest.mock('@tauri-apps/plugin-opener', () => ({
  revealItemInDir: (path: string) => mockRevealItemInDir(path),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

// Mock the player so we can drive onEnded and read the active title without
// dealing with real <video>/timers.
jest.mock('../NetflixStylePlayer', () => ({
  __esModule: true,
  default: ({ title, onEnded }: { title: string; onEnded?: () => void }) => (
    <div>
      <div data-testid="player-title">{title}</div>
      <button data-testid="fire-ended" onClick={() => onEnded?.()}>
        ended
      </button>
    </div>
  ),
}));

const makeVideo = (id: string): Video => ({
  id,
  path: `C:\\videos\\${id}.mp4`,
  thumbnailPath: null,
  folder_id: 'folder-1',
  metadata: {
    name: `${id}.mp4`,
    date_created: '2026-01-01T00:00:00',
    width: 1920,
    height: 1080,
    duration: 60,
    fps: 30,
    file_location: `C:\\videos\\${id}.mp4`,
    file_size: 1024,
    item_type: 'video/mp4',
  },
  isFavourite: false,
});

const videos = [makeVideo('a'), makeVideo('b'), makeVideo('c')];

const renderOverlay = (startIndex = 0) => {
  const store = configureStore({ reducer: rootReducer });
  store.dispatch(setVideos(videos));
  store.dispatch(setCurrentViewIndex(startIndex));
  const utils = render(
    <Provider store={store}>
      <VideoPlayerOverlay videos={videos} />
    </Provider>,
  );
  return { store, ...utils };
};

describe('VideoPlayerOverlay', () => {
  beforeEach(() => {
    mockToggleFavourite.mockClear();
    mockRevealItemInDir.mockClear();
  });

  test('shows the currently selected video', () => {
    renderOverlay(0);
    expect(screen.getByTestId('player-title')).toHaveTextContent('a.mp4');
  });

  test('arrows navigate to previous/next video', () => {
    renderOverlay(0);
    fireEvent.click(screen.getByRole('button', { name: 'Next video' }));
    expect(screen.getByTestId('player-title')).toHaveTextContent('b.mp4');
    fireEvent.click(screen.getByRole('button', { name: 'Previous video' }));
    expect(screen.getByTestId('player-title')).toHaveTextContent('a.mp4');
  });

  test('does not advance on end when auto-play is off (default)', () => {
    renderOverlay(0);
    fireEvent.click(screen.getByTestId('fire-ended'));
    expect(screen.getByTestId('player-title')).toHaveTextContent('a.mp4');
  });

  test('auto-play advances to the next video when a video ends', () => {
    renderOverlay(0);
    // Default label is off
    const toggle = screen.getByRole('button', {
      name: 'Toggle auto-play next',
    });
    expect(toggle).toHaveTextContent('Auto-play');
    expect(toggle).not.toHaveTextContent('Auto-play On');

    fireEvent.click(toggle);
    expect(
      screen.getByRole('button', { name: 'Toggle auto-play next' }),
    ).toHaveTextContent('Auto-play On');

    fireEvent.click(screen.getByTestId('fire-ended'));
    expect(screen.getByTestId('player-title')).toHaveTextContent('b.mp4');
  });

  test('auto-play does not wrap past the last video', () => {
    renderOverlay(2);
    fireEvent.click(
      screen.getByRole('button', { name: 'Toggle auto-play next' }),
    );
    fireEvent.click(screen.getByTestId('fire-ended'));
    expect(screen.getByTestId('player-title')).toHaveTextContent('c.mp4');
  });

  test('favourite button toggles the current video', () => {
    renderOverlay(0);
    fireEvent.click(screen.getByRole('button', { name: 'Add to favourites' }));
    expect(mockToggleFavourite).toHaveBeenCalledWith('a');
  });

  test('open folder reveals the current video path', () => {
    renderOverlay(0);
    fireEvent.click(screen.getByRole('button', { name: 'Open Folder' }));
    expect(mockRevealItemInDir).toHaveBeenCalledWith('C:\\videos\\a.mp4');
  });

  test('info toggle opens the details panel', () => {
    renderOverlay(0);
    expect(screen.queryByText('Video Details')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show Info' }));
    expect(screen.getByText('Video Details')).toBeInTheDocument();
  });

  test('escape closes the viewer', () => {
    const { store } = renderOverlay(0);
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    expect(store.getState().videos.currentViewIndex).toBe(-1);
  });
});
