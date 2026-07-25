import videoReducer, {
  setVideos,
  setCurrentViewIndex,
  closeVideoView,
  updateVideoFavoriteStatus,
  clearVideos,
} from '../videoSlice';
import { Video } from '@/types/Media';

const makeVideo = (id: string): Video => ({
  id,
  path: `C:\\videos\\${id}.mp4`,
  thumbnailPath: null,
  folder_id: 'folder-1',
  isFavourite: false,
});

describe('videoSlice', () => {
  const initialState = { videos: [], currentViewIndex: -1 };

  test('setVideos replaces the list', () => {
    const videos = [makeVideo('a'), makeVideo('b')];
    const state = videoReducer(initialState, setVideos(videos));
    expect(state.videos).toHaveLength(2);
  });

  test('setCurrentViewIndex accepts valid indexes and rejects invalid ones', () => {
    const withVideos = videoReducer(initialState, setVideos([makeVideo('a')]));

    let state = videoReducer(withVideos, setCurrentViewIndex(0));
    expect(state.currentViewIndex).toBe(0);

    state = videoReducer(state, setCurrentViewIndex(5));
    expect(state.currentViewIndex).toBe(0);
  });

  test('closeVideoView resets the index', () => {
    const withVideos = videoReducer(initialState, setVideos([makeVideo('a')]));
    const opened = videoReducer(withVideos, setCurrentViewIndex(0));
    const state = videoReducer(opened, closeVideoView());
    expect(state.currentViewIndex).toBe(-1);
  });

  test('updateVideoFavoriteStatus flips isFavourite', () => {
    const withVideos = videoReducer(initialState, setVideos([makeVideo('a')]));
    let state = videoReducer(withVideos, updateVideoFavoriteStatus('a'));
    expect(state.videos[0].isFavourite).toBe(true);
    state = videoReducer(state, updateVideoFavoriteStatus('a'));
    expect(state.videos[0].isFavourite).toBe(false);
  });

  test('clearVideos empties the list and resets the index', () => {
    const withVideos = videoReducer(initialState, setVideos([makeVideo('a')]));
    const opened = videoReducer(withVideos, setCurrentViewIndex(0));
    const state = videoReducer(opened, clearVideos());
    expect(state.videos).toHaveLength(0);
    expect(state.currentViewIndex).toBe(-1);
  });
});
