import { fireEvent, render, screen, waitFor } from '@/test-utils';
import { MultiPersonSearchDialog } from '@/components/Dialog/MultiPersonSearchDialog';
import * as apiFunctions from '@/api/api-functions/face_clusters';

jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: (path: string) => path,
}));

jest.mock('@/api/api-functions/face_clusters', () => ({
  fetchMultiPersonSearch: jest.fn(),
}));

const fetchMultiPersonSearch = apiFunctions.fetchMultiPersonSearch as jest.Mock;

const clusters = [
  {
    cluster_id: 'alice',
    cluster_name: 'Alice',
    face_count: 4,
    video_count: 1,
  },
];

const matchingVideo = {
  id: 'vid-1',
  path: '/videos/clip.mp4',
  thumbnailPath: '/thumbs/clip.jpg',
  folder_id: '1',
  isFavourite: false,
  tags: [],
  match_count: 1,
  metadata: {
    name: 'clip.mp4',
    date_created: null,
    width: 1920,
    height: 1080,
    duration: 8,
    file_location: 'clip.mp4',
    file_size: 1024,
    item_type: 'video/mp4',
  },
};

const renderDialog = () =>
  render(<MultiPersonSearchDialog open onOpenChange={jest.fn()} />, {
    preloadedState: { faceClusters: { clusters } } as never,
  });

beforeEach(() => fetchMultiPersonSearch.mockReset());

describe('MultiPersonSearchDialog', () => {
  test('puts matching videos in the store so the results page can show them', async () => {
    fetchMultiPersonSearch.mockResolvedValue({
      success: true,
      data: { images: [], videos: [matchingVideo], total: 0, total_videos: 1 },
    });

    const { store } = renderDialog();
    fireEvent.click(screen.getByRole('button', { name: /Alice/ }));
    fireEvent.click(screen.getByRole('button', { name: /^Search/ }));

    await waitFor(() => {
      expect(store.getState().videos.videos).toHaveLength(1);
    });
    expect(store.getState().videos.videos[0].id).toBe('vid-1');
  });

  test('videos alone still count as a match', async () => {
    fetchMultiPersonSearch.mockResolvedValue({
      success: true,
      data: { images: [], videos: [matchingVideo], total: 0, total_videos: 1 },
    });

    const { store } = renderDialog();
    fireEvent.click(screen.getByRole('button', { name: /Alice/ }));
    fireEvent.click(screen.getByRole('button', { name: /^Search/ }));

    await waitFor(() => {
      expect(store.getState().videos.videos).toHaveLength(1);
    });
    // The "No Matches Found" dialog must not have fired for a video-only hit.
    expect(store.getState().infoDialog?.isOpen).toBeFalsy();
  });
});
