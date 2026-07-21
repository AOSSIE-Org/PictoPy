import { render, screen, fireEvent } from '@testing-library/react';
import { VideoCard, formatVideoDuration } from '../VideoCard';
import { Video } from '@/types/Media';

// Mock Tauri convertFileSrc API
jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => `tauri-converted://${path}`,
}));

const mockToggleFavourite = jest.fn();
jest.mock('@/hooks/useToggleVideoFav', () => ({
  useToggleVideoFav: () => ({
    toggleFavourite: mockToggleFavourite,
    toggleFavouritePending: false,
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

describe('formatVideoDuration', () => {
  test('formats minutes and seconds', () => {
    expect(formatVideoDuration(75)).toBe('1:15');
  });

  test('formats hours', () => {
    expect(formatVideoDuration(3725)).toBe('1:02:05');
  });

  test('returns null for missing or invalid durations', () => {
    expect(formatVideoDuration(undefined)).toBeNull();
    expect(formatVideoDuration(null)).toBeNull();
    expect(formatVideoDuration(0)).toBeNull();
    expect(formatVideoDuration(Infinity)).toBeNull();
  });
});

describe('VideoCard', () => {
  beforeEach(() => {
    mockToggleFavourite.mockClear();
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

  test('invokes onClick when the card is clicked', () => {
    const onClick = jest.fn();
    const { container } = render(
      <VideoCard video={makeVideo()} onClick={onClick} />,
    );

    fireEvent.click(container.firstChild as HTMLElement);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  test('favourite button toggles without triggering card click', () => {
    const onClick = jest.fn();
    render(<VideoCard video={makeVideo()} onClick={onClick} />);

    fireEvent.click(screen.getByRole('button', { name: 'Favourite' }));
    expect(mockToggleFavourite).toHaveBeenCalledWith('vid-1');
    expect(onClick).not.toHaveBeenCalled();
  });
});
