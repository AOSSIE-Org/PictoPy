import { Routes, Route } from 'react-router';
import { render, screen, waitFor } from '@/test-utils';
import { FaceSearchResults } from '../FaceSearchResults/FaceSearchResults';
import {
  fetchSearchedFaces,
  fetchSearchedFacesBase64,
} from '@/api/api-functions';

jest.mock('@/api/api-functions', () => ({
  fetchSearchedFaces: jest.fn(),
  fetchSearchedFacesBase64: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

const IMAGES = [
  { id: '1', path: '/img1.jpg', thumbnailPath: '/thumb1.jpg', tags: [] },
  { id: '2', path: '/img2.jpg', thumbnailPath: '/thumb2.jpg', tags: [] },
];

const renderPage = (queryImage?: string) =>
  render(
    <Routes>
      <Route path="/face-search" element={<FaceSearchResults />} />
      <Route path="/home" element={<div>Home Page</div>} />
    </Routes>,
    {
      initialRoutes: ['/face-search'],
      preloadedState: {
        search: { active: !!queryImage, queryImage },
      },
    },
  );

describe('FaceSearchResults Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('searches by path and shows matching images', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('/photos/me.jpg');

    await waitFor(() =>
      expect(fetchSearchedFaces).toHaveBeenCalledWith({
        path: '/photos/me.jpg',
      }),
    );
    expect(screen.getByText(/Results for/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getAllByRole('img').length).toBeGreaterThan(1),
    );
    expect(screen.queryByText(/Search Failed/i)).not.toBeInTheDocument();
  });

  test('shows an inline error instead of a popup when the search fails', async () => {
    (fetchSearchedFaces as jest.Mock).mockRejectedValue(
      new Error('Network Error'),
    );

    renderPage('/photos/me.jpg');

    await waitFor(() =>
      expect(screen.getByText('Search Failed')).toBeInTheDocument(),
    );
    expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument();
  });

  test('shows matching videos in their own section', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
      videos: [
        {
          id: 'v1',
          path: '/clip.mp4',
          thumbnailPath: '/clip-thumb.jpg',
          folder_id: '1',
          tags: [],
          metadata: { name: 'clip.mp4' },
        },
      ],
    });

    renderPage('/photos/me.jpg');

    await waitFor(() => {
      expect(screen.getByText('Videos')).toBeInTheDocument();
      expect(screen.getByLabelText(/Play clip.mp4/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByText(/No matching faces found/i),
    ).not.toBeInTheDocument();
  });

  test('shows an empty state when no faces match', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: [],
    });

    renderPage('/photos/me.jpg');

    await waitFor(() =>
      expect(
        screen.getByText(/No matching faces found in your gallery/i),
      ).toBeInTheDocument(),
    );
  });

  test('uses the base64 endpoint for webcam captures', async () => {
    (fetchSearchedFacesBase64 as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('data:image/png;base64,AAAA');

    await waitFor(() =>
      expect(fetchSearchedFacesBase64).toHaveBeenCalledWith({
        base64_data: 'data:image/png;base64,AAAA',
      }),
    );
    expect(fetchSearchedFaces).not.toHaveBeenCalled();
  });

  test('goes back Home when there is no search photo', async () => {
    renderPage(undefined);

    await waitFor(() =>
      expect(screen.getByText('Home Page')).toBeInTheDocument(),
    );
    expect(fetchSearchedFaces).not.toHaveBeenCalled();
  });
});
