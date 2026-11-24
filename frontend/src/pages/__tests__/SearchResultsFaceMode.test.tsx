import { Routes, Route } from 'react-router';
import { fireEvent } from '@testing-library/react';
import { render, screen, waitFor } from '@/test-utils';
import { SearchResults } from '../SearchResults/SearchResults';
import {
  fetchDetectedFaces,
  fetchDetectedFacesBase64,
  fetchSearchedFaces,
  fetchSearchedFacesBase64,
  searchImagesByTag,
  searchVideosByTag,
} from '@/api/api-functions';

jest.mock('@/api/api-functions', () => ({
  fetchDetectedFaces: jest.fn(),
  fetchDetectedFacesBase64: jest.fn(),
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

const face = (index: number, x: number) => ({
  index,
  bbox: { x, y: 50, width: 100, height: 100 },
  confidence: 0.9,
});

const detected = (faces: ReturnType<typeof face>[], facesSkipped = 0) => ({
  success: true,
  message: `Detected ${faces.length} faces.`,
  data: {
    image_width: 1000,
    image_height: 500,
    faces,
    faces_skipped: facesSkipped,
  },
});

const ONE_FACE = detected([face(0, 100)]);
const TWO_FACES = detected([face(0, 100), face(1, 500)]);

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
        search: { queryImage },
      },
    },
  );

describe('SearchResults face mode', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // A photo with one face is searched straight away, as before.
    (fetchDetectedFaces as jest.Mock).mockResolvedValue(ONE_FACE);
    (fetchDetectedFacesBase64 as jest.Mock).mockResolvedValue(ONE_FACE);
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

  test('ignores a text value in the URL and only runs the face search', async () => {
    (fetchSearchedFaces as jest.Mock).mockResolvedValue({
      success: true,
      data: IMAGES,
    });

    renderPage('/photos/me.jpg', ['/search?mode=face&value=tree']);

    await waitFor(() => expect(fetchSearchedFaces).toHaveBeenCalled());
    expect(searchImagesByTag).not.toHaveBeenCalled();
    expect(searchVideosByTag).not.toHaveBeenCalled();
  });

  describe('choosing faces in a group photo', () => {
    const pick = (name: string) =>
      fireEvent.click(screen.getByRole('button', { name }));
    const search = () =>
      fireEvent.click(screen.getByRole('button', { name: /^Search/ }));

    beforeEach(() => {
      (fetchDetectedFaces as jest.Mock).mockResolvedValue(TWO_FACES);
      (fetchSearchedFaces as jest.Mock).mockResolvedValue({
        success: true,
        data: IMAGES,
      });
    });

    test('a one-face photo skips the picker', async () => {
      (fetchDetectedFaces as jest.Mock).mockResolvedValue(ONE_FACE);

      renderPage('/photos/me.jpg');

      await waitFor(() => expect(fetchSearchedFaces).toHaveBeenCalled());
      expect(
        screen.queryByText('Who do you want to find?'),
      ).not.toBeInTheDocument();
    });

    test('a group photo waits for a pick before searching', async () => {
      renderPage('/photos/group.jpg');

      expect(
        await screen.findByText('Who do you want to find?'),
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: 'Face 1' }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: 'Face 2' }),
      ).toBeInTheDocument();
      expect(fetchSearchedFaces).not.toHaveBeenCalled();
    });

    test('searches with the face the user picked', async () => {
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');

      pick('Face 2');
      search();

      await waitFor(() =>
        expect(fetchSearchedFaces).toHaveBeenCalledWith({
          path: '/photos/group.jpg',
          face_indices: [1],
          match_mode: 'match_any',
        }),
      );
      expect(
        await screen.findByText('Searching for the 1 face you picked.'),
      ).toBeInTheDocument();
      expect(
        screen.queryByText('Who do you want to find?'),
      ).not.toBeInTheDocument();
    });

    test('passes match_all when the user asks for everyone together', async () => {
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');

      pick('Face 1');
      pick('Face 2');
      fireEvent.click(screen.getByRole('switch'));
      search();

      await waitFor(() =>
        expect(fetchSearchedFaces).toHaveBeenCalledWith({
          path: '/photos/group.jpg',
          face_indices: [0, 1],
          match_mode: 'match_all',
        }),
      );
      expect(
        await screen.findByText(
          'Photos and videos with all of the 2 faces you picked.',
        ),
      ).toBeInTheDocument();
    });

    test('lets the user choose different faces after seeing results', async () => {
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');
      pick('Face 1');
      search();
      fireEvent.click(
        await screen.findByRole('button', { name: 'Choose different faces' }),
      );

      expect(
        await screen.findByText('Who do you want to find?'),
      ).toBeInTheDocument();
      expect(fetchSearchedFaces).toHaveBeenCalledTimes(1);

      pick('Face 2');
      search();

      await waitFor(() =>
        expect(fetchSearchedFaces).toHaveBeenLastCalledWith({
          path: '/photos/group.jpg',
          face_indices: [1],
          match_mode: 'match_any',
        }),
      );
    });

    test('explains an empty result for everyone together', async () => {
      (fetchSearchedFaces as jest.Mock).mockResolvedValue({
        success: true,
        data: [],
      });
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');

      pick('Face 1');
      pick('Face 2');
      fireEvent.click(screen.getByRole('switch'));
      search();

      expect(
        await screen.findByText(/No photo or video has all 2 of these faces/i),
      ).toBeInTheDocument();
    });

    test('shows the picked faces instead of the whole group photo', async () => {
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');

      pick('Face 1');
      pick('Face 2');
      search();

      await screen.findByText(/any of the 2 faces you picked/i);
      expect(screen.getAllByAltText('Searched face')).toHaveLength(2);
    });

    test('still offers to choose again when nothing matched', async () => {
      (fetchSearchedFaces as jest.Mock).mockResolvedValue({
        success: true,
        data: [],
      });
      renderPage('/photos/group.jpg');
      await screen.findByText('Who do you want to find?');

      pick('Face 1');
      search();

      expect(
        await screen.findByText(/No matching faces found in your gallery/i),
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: 'Choose different faces' }),
      ).toBeInTheDocument();
    });

    test('uses the base64 routes for a webcam capture', async () => {
      (fetchDetectedFacesBase64 as jest.Mock).mockResolvedValue(TWO_FACES);
      (fetchSearchedFacesBase64 as jest.Mock).mockResolvedValue({
        success: true,
        data: IMAGES,
      });

      renderPage('data:image/png;base64,AAAA');
      await screen.findByText('Who do you want to find?');
      pick('Face 2');
      search();

      expect(fetchDetectedFacesBase64).toHaveBeenCalledWith({
        base64_data: 'data:image/png;base64,AAAA',
      });
      await waitFor(() =>
        expect(fetchSearchedFacesBase64).toHaveBeenCalledWith({
          base64_data: 'data:image/png;base64,AAAA',
          face_indices: [1],
          match_mode: 'match_any',
        }),
      );
      expect(fetchDetectedFaces).not.toHaveBeenCalled();
      expect(fetchSearchedFaces).not.toHaveBeenCalled();
    });

    test('says so when the photo has no faces, without searching', async () => {
      (fetchDetectedFaces as jest.Mock).mockResolvedValue(detected([]));

      renderPage('/photos/landscape.jpg');

      expect(
        await screen.findByText('No faces were detected in this photo.'),
      ).toBeInTheDocument();
      expect(fetchSearchedFaces).not.toHaveBeenCalled();
    });

    test('shows an inline error when detecting the faces fails', async () => {
      (fetchDetectedFaces as jest.Mock).mockRejectedValue(
        new Error('Network Error'),
      );

      renderPage('/photos/group.jpg');

      expect(await screen.findByText('Search Failed')).toBeInTheDocument();
      expect(fetchSearchedFaces).not.toHaveBeenCalled();
    });

    test('shows the backend message when it reports a failure', async () => {
      (fetchDetectedFaces as jest.Mock).mockResolvedValue({
        success: false,
        message: 'Failed to process image: model missing',
      });

      renderPage('/photos/group.jpg');

      expect(
        await screen.findByText('Failed to process image: model missing'),
      ).toBeInTheDocument();
      expect(fetchSearchedFaces).not.toHaveBeenCalled();
    });
  });
});
