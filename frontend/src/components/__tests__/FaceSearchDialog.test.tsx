import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/test-utils';
import { closeVideoView } from '@/features/videoSlice';
import { startSearch } from '@/features/searchSlice';
import { FaceSearchDialog } from '@/components/Dialog/FaceSearchDialog';

jest.mock('@/hooks/selectFile', () => ({
  useFile: () => ({
    pickSingleFile: jest.fn().mockResolvedValue('/photos/search.jpg'),
  }),
}));

jest.mock('@/components/WebCam/WebCamComponent', () => () => null);

describe('FaceSearchDialog', () => {
  it('closes a stale video view before starting a face search', async () => {
    const user = userEvent.setup();
    const { store } = render(<FaceSearchDialog />, {
      preloadedState: {
        videos: {
          videos: [
            {
              id: 'video-1',
              path: '/videos/one.mp4',
              thumbnailPath: null,
              folder_id: 'folder-1',
            },
          ],
          currentViewIndex: 0,
        },
      },
    });
    const dispatch = jest.spyOn(store, 'dispatch');

    await user.click(
      screen.getByRole('button', { name: /Face Detection Search/ }),
    );
    await user.click(screen.getByRole('button', { name: /Upload Photo/ }));

    await waitFor(() =>
      expect(store.getState().search.queryImage).toBe('/photos/search.jpg'),
    );
    const actionTypes = dispatch.mock.calls.map(([action]) => action.type);
    const closeIndex = actionTypes.indexOf(closeVideoView.type);
    const searchIndex = actionTypes.indexOf(startSearch.type);
    expect(closeIndex).toBeGreaterThanOrEqual(0);
    expect(searchIndex).toBeGreaterThan(closeIndex);
    expect(store.getState().videos.currentViewIndex).toBe(-1);
  });
});
