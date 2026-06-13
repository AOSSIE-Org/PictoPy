import { render, screen, waitFor } from '@/test-utils';
import { Routes, Route } from 'react-router';
import { PersonImages } from '@/pages/PersonImages/PersonImages';
import type { Image } from '@/types/Media';
import * as apiFunctions from '@/api/api-functions';

// ImageCard resolves thumbnails through Tauri's convertFileSrc; return the path
// unchanged so we can assert which person's images are in the DOM by their src.
jest.mock('@tauri-apps/api/core', () => ({
  invoke: jest.fn().mockResolvedValue(null),
  convertFileSrc: (path: string) => path,
}));

jest.mock('@/api/api-functions', () => ({
  fetchClusterImages: jest.fn(),
  renameCluster: jest.fn(),
}));

const fetchClusterImages = apiFunctions.fetchClusterImages as jest.Mock;

const makeImage = (id: string, path: string): Image => ({
  id,
  path,
  thumbnailPath: path,
  folder_id: 'folder',
  isTagged: true,
  isFavourite: false,
  tags: [],
});

// "Person A" stands in for whatever the previous page (e.g. the Home gallery)
// left in the shared `images` slice; "Person B" is the cluster we navigate to.
const personAImages = [
  makeImage('a1', '/personA/1.jpg'),
  makeImage('a2', '/personA/2.jpg'),
];
const personBImages = [
  makeImage('b1', '/personB/1.jpg'),
  makeImage('b2', '/personB/2.jpg'),
];

const renderPerson = (clusterId: string) =>
  render(
    <Routes>
      <Route path="/person/:clusterId" element={<PersonImages />} />
    </Routes>,
    {
      // Pre-seed the shared slice with the previous page's images. This is the
      // exact condition that produced the flash described in issue #1315.
      preloadedState: {
        images: { images: personAImages, currentViewIndex: -1 },
      },
      initialRoutes: [`/person/${clusterId}`],
    },
  );

const imageSrcs = (container: HTMLElement) =>
  Array.from(container.querySelectorAll('img')).map((img) =>
    img.getAttribute('src'),
  );

const hasPersonA = (container: HTMLElement) =>
  imageSrcs(container).some((src) => src?.startsWith('/personA/'));
const hasPersonB = (container: HTMLElement) =>
  imageSrcs(container).some((src) => src?.startsWith('/personB/'));

beforeEach(() => {
  fetchClusterImages.mockReset();
  fetchClusterImages.mockImplementation(async ({ clusterId }) => ({
    success: true,
    data: {
      images: clusterId === 'B' ? personBImages : personAImages,
      cluster_name: clusterId === 'B' ? 'Bob' : 'Alice',
    },
  }));
});

describe('PersonImages (issue #1315: no flash of the previous page)', () => {
  test('never paints the stale slice images, on the first frame or after', async () => {
    const { container } = renderPerson('B');

    // First frame: before the cluster query resolves, the shared slice still
    // holds Person A's images. The grid must not paint them, otherwise the user
    // sees the flash. (This assertion fails against the pre-fix code.)
    expect(hasPersonA(container)).toBe(false);

    // Let the query resolve, then confirm Person A never appears at any point.
    await waitFor(() => {
      expect(hasPersonB(container)).toBe(true);
    });
    expect(hasPersonA(container)).toBe(false);
  });

  test("renders the navigated cluster's images and name once loaded", async () => {
    const { container } = renderPerson('B');

    expect(await screen.findByText('Bob')).toBeInTheDocument();
    await waitFor(() => {
      expect(hasPersonB(container)).toBe(true);
    });
  });
});
