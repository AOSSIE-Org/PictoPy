import { render, screen, fireEvent } from '@testing-library/react';
import { VideoCard } from '../VideoCard';
import { Video } from '@/types/Media';

// Mock Tauri convertFileSrc API
jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

const mockToggleFavourite = jest.fn();
let mockFavouritePending = false;
jest.mock('@/hooks/useToggleVideoFav', () => ({
  useToggleVideoFav: () => ({
    toggleFavourite: mockToggleFavourite,
    toggleFavouritePending: mockFavouritePending,
  }),
}));

const makeVideo = (overrides: Partial<Video> = {}): Video => ({
  id: 'vid-1',
  path: 'C:\\videos\\sample.mp4',
  thumbnailPath: 'C:\\thumbnails\\thumbnail_vid-1.jpg',
  folder_id: 'folder-1',
  metadata: {
    name: 'sample.mp4',
    date_created: '2026-01-01T00:00:00',
    width: 1920,
    height: 1080,
    duration: 75,
    fps: 30,
    file_location: 'C:\\videos\\sample.mp4',
    file_size: 1024,
    item_type: 'video/mp4',
  },
  isFavourite: false,
  ...overrides,
});

describe('VideoCard', () => {
  beforeEach(() => {
    mockToggleFavourite.mockClear();
    mockFavouritePending = false;
  });

  test('renders converted thumbnail and duration badge', () => {
    render(<VideoCard video={makeVideo()} />);

    const img = screen.getByAltText('sample.mp4') as HTMLImageElement;
    expect(img.src).toContain('tauri-converted://');
    expect(img.src).toContain('thumbnail_vid-1.jpg');
    expect(screen.getByText('1:15')).toBeInTheDocument();
  });

  test('renders placeholder instead of img when thumbnailPath is null', () => {
    render(<VideoCard video={makeVideo({ thumbnailPath: null })} />);

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  test('invokes onClick when the play control is activated', () => {
    const onClick = jest.fn();
    render(<VideoCard video={makeVideo()} onClick={onClick} />);

    fireEvent.click(screen.getByRole('button', { name: 'Play sample.mp4' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  test('favourite button toggles without triggering card click', () => {
    const onClick = jest.fn();
    render(<VideoCard video={makeVideo()} onClick={onClick} />);

    fireEvent.click(screen.getByRole('button', { name: 'Favourite' }));
    expect(mockToggleFavourite).toHaveBeenCalledWith('vid-1');
    expect(onClick).not.toHaveBeenCalled();
  });

  test('exposes playback as a native button so keyboard activation is free', () => {
    render(<VideoCard video={makeVideo()} onClick={jest.fn()} />);

    const play = screen.getByRole('button', { name: 'Play sample.mp4' });
    expect(play.tagName).toBe('BUTTON');
    // The favourite control must be a sibling, never nested inside playback
    expect(
      play.contains(screen.getByRole('button', { name: 'Favourite' })),
    ).toBe(false);
  });

  test('renders no playback control or play glyph without an action', () => {
    const { container } = render(<VideoCard video={makeVideo()} />);

    expect(
      screen.queryByRole('button', { name: /^Play / }),
    ).not.toBeInTheDocument();
    // The card must not look playable when it isn't
    expect(container.querySelector('.lucide-play')).not.toBeInTheDocument();
  });

  test('shows the play glyph when the card is playable', () => {
    const { container } = render(
      <VideoCard video={makeVideo()} onClick={jest.fn()} />,
    );
    expect(container.querySelector('.lucide-play')).toBeInTheDocument();
  });

  test('falls back to the placeholder when the thumbnail fails to load', () => {
    render(<VideoCard video={makeVideo()} />);

    const img = screen.getByAltText('sample.mp4');
    fireEvent.error(img);

    expect(screen.queryByAltText('sample.mp4')).not.toBeInTheDocument();
  });

  test('favourite button is disabled while a toggle is in flight', () => {
    mockFavouritePending = true;
    render(<VideoCard video={makeVideo()} />);

    const favourite = screen.getByRole('button', { name: 'Favourite' });
    expect(favourite).toBeDisabled();
    expect(favourite).toHaveAttribute('aria-busy', 'true');

    fireEvent.click(favourite);
    expect(mockToggleFavourite).not.toHaveBeenCalled();
  });
});
