import { useLayoutEffect } from 'react';
import { fireEvent, render, screen, waitFor } from '@/test-utils';
import { Routes, Route, useNavigate } from 'react-router';
import { PersonImages } from '@/pages/PersonImages/PersonImages';
import type { Image } from '@/types/Media';
import * as apiFunctions from '@/api/api-functions';

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

const personAImages = [
  makeImage('a1', '/personA/1.jpg'),
  makeImage('a2', '/personA/2.jpg'),
];
const personBImages = [
  makeImage('b1', '/personB/1.jpg'),
  makeImage('b2', '/personB/2.jpg'),
];

const CommitProbe = ({
  onCommit,
}: {
  onCommit?: (headingText: string | null) => void;
}) => {
  useLayoutEffect(() => {
    onCommit?.(document.querySelector('h1')?.textContent ?? null);
  });

  return null;
};

const PersonImagesWithNavigation = ({
  onCommit,
}: {
  onCommit?: (headingText: string | null) => void;
}) => {
  const navigate = useNavigate();

  return (
    <>
      <button type="button" onClick={() => navigate('/person/B')}>
        Go to Person B
      </button>
      <PersonImages />
      <CommitProbe onCommit={onCommit} />
    </>
  );
};

const renderPerson = (
  clusterId: string,
  options: {
    withNavigation?: boolean;
    onCommit?: (headingText: string | null) => void;
  } = {},
) =>
  render(
    <Routes>
      <Route
        path="/person/:clusterId"
        element={
          options.withNavigation ? (
            <PersonImagesWithNavigation onCommit={options.onCommit} />
          ) : (
            <PersonImages />
          )
        }
      />
    </Routes>,
    {
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
  test('never paints stale images or heading when navigating to a cached person', async () => {
    const committedHeadings: Array<string | null> = [];
    const { container, queryClient } = renderPerson('A', {
      withNavigation: true,
      onCommit: (headingText) => committedHeadings.push(headingText),
    });

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Alice' }),
      ).toBeInTheDocument();
      expect(hasPersonA(container)).toBe(true);
    });

    queryClient.setQueryData(['person-images', 'B'], {
      success: true,
      data: {
        images: personBImages,
        cluster_name: 'Bob',
      },
    });

    committedHeadings.length = 0;
    fireEvent.click(screen.getByRole('button', { name: 'Go to Person B' }));

    expect(committedHeadings).not.toContain('Alice');
    expect(
      screen.queryByRole('heading', { name: 'Alice' }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Bob' })).toBeInTheDocument();
    expect(hasPersonA(container)).toBe(false);
    expect(hasPersonB(container)).toBe(true);
  });

  test("renders the navigated cluster's images and name once loaded", async () => {
    const { container } = renderPerson('B');

    expect(
      screen.queryByRole('heading', { name: 'Alice' }),
    ).not.toBeInTheDocument();
    expect(hasPersonA(container)).toBe(false);

    expect(await screen.findByText('Bob')).toBeInTheDocument();
    await waitFor(() => {
      expect(hasPersonB(container)).toBe(true);
    });
  });
});
