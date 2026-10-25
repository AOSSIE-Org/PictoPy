import { Routes, Route } from 'react-router';
import { fireEvent } from '@testing-library/react';
import { render, screen, waitFor } from '@/test-utils';
import { SearchResults } from '../SearchResults/SearchResults';
import {
  fetchSearchedFaces,
  fetchSearchedFacesBase64,
} from '@/api/api-functions';

jest.mock('@/api/api-functions', () => ({
  fetchSearchedFaces: jest.fn(),
  fetchSearchedFacesBase64: jest.fn(),
  searchImagesByTag: jest.fn(),
  semanticSearchImages: jest.fn(),
  searchVideosByTag: jest.fn(),
  semanticSearchVideos: jest.fn(),
  fetchModelStatus: jest.fn().mockResolvedValue({ success: true, data: {} }),
  fetchAllClusters: jest.fn().mockResolvedValue({
    success: true,
    data: { clusters: [] },
  }),
  fetchMultiPersonSearch: jest.fn(),
}));

jest.mock('@tauri-apps/api/core', () => ({
  convertFileSrc: (path: string) => path,
}));

const IMAGES = [
  { id: '1', path: '/img1.jpg', thumbnailPath: '/thumb1.jpg', tags: [] },
  { id: '2', path: '/img2.jpg', thumbnailPath: '/thumb2.jpg', tags: [] },
];

const renderPage = (
  queryImage?: string,
  initialRoutes = ['/search?mode=face'],
) =>
  render(
    <Routes>
      <Route path="/search" element={<SearchResults />} />
      <Route path="/home" element={<div>Home Page</div>} />
    </Routes>,
    {
      initialRoutes,
      preloadedState: {
        search: { active: !!queryImage, queryImage },
      },
    },
  );

describe('SearchResults face mode', () => {
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

  test('Back goes Home when there is no earlier history entry', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('/photos/me.jpg');

    fireEvent.click(await screen.findByRole('button', { name: /Back/i }));

    expect(await screen.findByText('Home Page')).toBeInTheDocument();
  });

  test('Back returns to the previous page when there is history', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('/photos/me.jpg', ['/home', '/search?mode=face']);

    fireEvent.click(await screen.findByRole('button', { name: /Back/i }));

    expect(await screen.findByText('Home Page')).toBeInTheDocument();
  });

  test('hides the query thumbnail if it fails to load', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('/photos/missing.jpg');

    fireEvent.error(await screen.findByAltText('Searched face'));

    expect(screen.queryByAltText('Searched face')).not.toBeInTheDocument();
  });
});
