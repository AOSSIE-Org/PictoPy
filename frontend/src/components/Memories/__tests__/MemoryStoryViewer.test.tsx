import { screen, fireEvent } from '@testing-library/react';
import { render } from '@/test-utils';
import type { MemoryStory } from '@/api/api-functions/memories';
import { MemoryStoryViewer } from '../MemoryStoryViewer';

jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: jest.fn((path: string) => `asset://localhost/${path}`),
}));

const mockUpdateMemory = jest.fn();
let mockStory: MemoryStory | null = null;

jest.mock('@/hooks/useMemories', () => ({
  useMemory: () => ({
    successData: mockStory ? { memory: mockStory } : undefined,
    isLoading: false,
    isError: false,
  }),
  useUpdateMemory: () => ({ mutate: mockUpdateMemory }),
}));

const image = (id: string, sort_order: number) => ({
  id,
  path: `/photos/${id}.jpg`,
  thumbnailPath: null,
  captured_at: '2024-07-26T10:00:00',
  latitude: null,
  longitude: null,
  isFavourite: false,
  sort_order,
  score: 1,
});

const video = (id: string, sort_order: number) => ({
  id,
  path: `/videos/${id}.mp4`,
  thumbnailPath: null,
  captured_at: '2024-07-26T10:05:00',
  duration: 8,
  isFavourite: false,
  sort_order,
  score: 1,
});

const makeMockStory = (overrides: Partial<MemoryStory> = {}): MemoryStory =>
  ({
    memory_id: 'mem-1',
    dedupe_key: 'import:2024-07-26..2024-07-26',
    event_type: 'import_event',
    status: 'complete',
    title: 'Beach',
    subtitle: '26 July 2024',
    place_label: null,
    center_lat: null,
    center_lon: null,
    surface_date: '2024-07-26',
    period_start: '2024-07-26T10:00:00',
    period_end: '2024-07-26T10:05:00',
    image_count: 1,
    video_count: 1,
    cover_image_id: 'p1',
    cover_thumbnail_path: null,
    score: 0.5,
    notified_at: null,
    viewed_at: '2024-07-26T12:00:00',
    dismissed: false,
    created_at: null,
    images: [image('p1', 0)],
    videos: [video('v1', 1)],
    signals: null,
    ...overrides,
  }) as MemoryStory;

// The theme ships muted, so ducking is only observable with it on -- otherwise
// these assertions pass on the default and prove nothing.
const renderViewer = (themeAudible = false) =>
  render(<MemoryStoryViewer memoryId="mem-1" memories={[]} musicEnabled />, {
    preloadedState: {
      memories: {
        activeMemoryId: 'mem-1',
        slideIndex: 0,
        isPlaying: true,
        isMuted: !themeAudible,
        slideDurationMs: 5000,
      },
    },
  });

const clip = () => screen.getByTestId('memory-story-video') as HTMLVideoElement;
const theme = () => document.querySelector('audio') as HTMLAudioElement;

beforeAll(() => {
  // jsdom implements neither; the component only ever fires and forgets.
  window.HTMLMediaElement.prototype.play = jest
    .fn()
    .mockResolvedValue(undefined);
  window.HTMLMediaElement.prototype.pause = jest.fn();
});

beforeEach(() => {
  mockStory = makeMockStory();
  mockUpdateMemory.mockClear();
});

describe('MemoryStoryViewer with clips', () => {
  it('shows the still first and the clip after it', () => {
    renderViewer();

    expect(screen.queryByTestId('memory-story-video')).toBeNull();
    fireEvent.click(screen.getByLabelText('Next slide'));
    expect(clip()).toBeInTheDocument();
  });

  it('starts a clip muted', () => {
    // Every gallery does this. Sound is something the user asks for.
    renderViewer();
    fireEvent.click(screen.getByLabelText('Next slide'));

    expect(clip().muted).toBe(true);
  });

  it('gives a clip no player controls', () => {
    // A story slide is not a video player; play/pause belongs to the story.
    renderViewer();
    fireEvent.click(screen.getByLabelText('Next slide'));

    expect(clip().hasAttribute('controls')).toBe(false);
  });

  it('unmutes a clip on request', () => {
    renderViewer();
    fireEvent.click(screen.getByLabelText('Next slide'));

    fireEvent.click(screen.getByLabelText('Unmute this clip'));

    expect(clip().muted).toBe(false);
  });

  it('silences the theme while a clip is audible', () => {
    // Two soundtracks at once is nobody's intent.
    renderViewer(true);
    expect(theme().muted).toBe(false);
    fireEvent.click(screen.getByLabelText('Next slide'));

    fireEvent.click(screen.getByLabelText('Unmute this clip'));

    expect(theme().muted).toBe(true);
  });

  it('brings the theme back when the clip is muted again', () => {
    renderViewer(true);
    fireEvent.click(screen.getByLabelText('Next slide'));
    fireEvent.click(screen.getByLabelText('Unmute this clip'));

    fireEvent.click(screen.getByLabelText('Mute this clip'));

    expect(theme().muted).toBe(false);
  });

  it('does not carry a clip’s sound to the next slide', () => {
    mockStory = makeMockStory({
      images: [image('p1', 0), image('p2', 2)],
      videos: [video('v1', 1)],
      image_count: 2,
    });
    renderViewer();
    fireEvent.click(screen.getByLabelText('Next slide'));
    fireEvent.click(screen.getByLabelText('Unmute this clip'));

    fireEvent.click(screen.getByLabelText('Next slide'));
    fireEvent.click(screen.getByLabelText('Previous slide'));

    expect(clip().muted).toBe(true);
  });

  it('offers no sound toggle on a still', () => {
    renderViewer();
    expect(screen.queryByLabelText('Unmute this clip')).toBeNull();
  });
});

describe('MemoryStoryViewer before its slides arrive', () => {
  // With no slides every index is past the end, so navigating used to read as
  // "reached the last one" and dismissed the whole viewer.
  beforeEach(() => {
    mockStory = null;
  });

  it.each(['ArrowRight', 'ArrowLeft'])('ignores %s', (key) => {
    const { store } = renderViewer();
    fireEvent.keyDown(window, { key });
    expect(store.getState().memories.activeMemoryId).toBe('mem-1');
  });

  it('ignores a swipe', () => {
    const { store } = renderViewer();
    const dialog = screen.getByRole('dialog');

    fireEvent.pointerDown(dialog, { clientX: 300 });
    fireEvent.pointerUp(dialog, { clientX: 20 });

    expect(store.getState().memories.activeMemoryId).toBe('mem-1');
  });

  it('still closes on Escape', () => {
    const { store } = renderViewer();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(store.getState().memories.activeMemoryId).toBeNull();
  });
});
