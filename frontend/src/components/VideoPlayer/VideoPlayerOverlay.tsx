import { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { revealItemInDir } from '@tauri-apps/plugin-opener';
import { Video } from '@/types/Media';
import NetflixStylePlayer from './NetflixStylePlayer';
import { VideoViewerControls } from './VideoViewerControls';
import { VideoInfoPanel } from './VideoInfoPanel';
import { NavigationButtons } from '@/components/Media/NavigationButtons';
import { selectCurrentVideoIndex } from '@/features/videoSelectors';
import { setCurrentViewIndex, closeVideoView } from '@/features/videoSlice';
import { useToggleVideoFav } from '@/hooks/useToggleVideoFav';

interface VideoPlayerOverlayProps {
  videos: Video[];
}

export function VideoPlayerOverlay({ videos }: VideoPlayerOverlayProps) {
  const dispatch = useDispatch();
  const currentIndex = useSelector(selectCurrentVideoIndex);
  const { toggleFavourite } = useToggleVideoFav();
  const [showInfo, setShowInfo] = useState(false);
  // Off by default every time the viewer opens — never auto-advance unasked.
  const [autoPlayNext, setAutoPlayNext] = useState(false);

  const currentVideo =
    currentIndex >= 0 && currentIndex < videos.length
      ? videos[currentIndex]
      : null;

  const handleClose = useCallback(() => {
    dispatch(closeVideoView());
  }, [dispatch]);

  const handleNext = useCallback(() => {
    if (currentIndex < videos.length - 1) {
      dispatch(setCurrentViewIndex(currentIndex + 1));
    }
  }, [dispatch, currentIndex, videos.length]);

  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      dispatch(setCurrentViewIndex(currentIndex - 1));
    }
  }, [dispatch, currentIndex]);

  const handleEnded = useCallback(() => {
    if (autoPlayNext && currentIndex < videos.length - 1) {
      dispatch(setCurrentViewIndex(currentIndex + 1));
    }
  }, [autoPlayNext, currentIndex, videos.length, dispatch]);

  const handleOpenFolder = useCallback(async () => {
    if (!currentVideo?.path) return;
    try {
      await revealItemInDir(currentVideo.path);
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  }, [currentVideo]);

  const handleToggleFavourite = useCallback(() => {
    if (currentVideo?.id) {
      toggleFavourite(currentVideo.id);
    }
  }, [currentVideo, toggleFavourite]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleClose]);

  if (!currentVideo) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/95 backdrop-blur-lg">
      <VideoViewerControls
        showInfo={showInfo}
        onToggleInfo={() => setShowInfo((prev) => !prev)}
        onOpenFolder={handleOpenFolder}
        onToggleFavourite={handleToggleFavourite}
        isFavourite={currentVideo.isFavourite || false}
        autoPlayNext={autoPlayNext}
        onToggleAutoPlayNext={() => setAutoPlayNext((prev) => !prev)}
        onClose={handleClose}
      />

      <VideoInfoPanel
        show={showInfo}
        onClose={() => setShowInfo(false)}
        video={currentVideo}
        currentIndex={currentIndex}
        totalVideos={videos.length}
      />

      <div className="relative flex flex-1 items-center justify-center overflow-hidden px-6 pt-20 pb-6">
        <div className="w-full max-w-6xl">
          {/* key forces a clean remount so player state resets per video */}
          <NetflixStylePlayer
            key={currentVideo.id}
            videoSrc={currentVideo.path}
            title={currentVideo.metadata?.name ?? ''}
            description=""
            autoPlay
            onEnded={handleEnded}
          />
        </div>
        {videos.length > 1 && (
          <NavigationButtons
            onPrevious={handlePrevious}
            onNext={handleNext}
            previousLabel="Previous video"
            nextLabel="Next video"
          />
        )}
      </div>
    </div>
  );
}
