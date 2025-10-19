import { useState, useCallback, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { MediaViewProps } from '@/types/Media';
import {
  selectCurrentViewIndex,
  selectActiveImageList,
} from '@/features/imageSelectors';
import { setCurrentViewIndex, closeImageView } from '@/features/imageSlice';

// Modular components
import { MediaViewControls } from './MediaViewControls';
import { ZoomControls } from './ZoomControls';
import { MediaThumbnails } from './MediaThumbnails';
import { MediaInfoPanel } from './MediaInfoPanel';
import { ImageViewer } from './ImageViewer';
import { NavigationButtons } from './NavigationButtons';

// Custom hooks
import { useImageViewControls } from '@/hooks/useImageViewControls';
import { useSlideshow } from '@/hooks/useSlideshow';
import { useFavorites } from '@/hooks/useFavorites';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';

export function MediaView({ onClose, type = 'image' }: MediaViewProps) {
  const dispatch = useDispatch();

  // Redux selectors
  const images = useSelector(selectActiveImageList);
  const currentViewIndex = useSelector(selectCurrentViewIndex);
  const totalImages = images.length;
  const currentImage = useMemo(() => {
    if (currentViewIndex >= 0 && currentViewIndex < images.length) {
      return images[currentViewIndex];
    }
    return null;
  }, [images, currentViewIndex]);

  // Local UI state
  const [showInfo, setShowInfo] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);

  // Custom hooks
  const { viewState, handlers } = useImageViewControls();
  const { favorites, toggleFavorite, isFavorite } = useFavorites();

  // Navigation handlers
  const handleNextImage = useCallback(() => {
    if (currentViewIndex < images.length - 1) {
      dispatch(setCurrentViewIndex(currentViewIndex + 1));
      handlers.resetZoom();
    }
  }, [dispatch, handlers, currentViewIndex, images.length]);

  const handlePreviousImage = useCallback(() => {
    if (currentViewIndex > 0) {
      dispatch(setCurrentViewIndex(currentViewIndex - 1));
      handlers.resetZoom();
    }
  }, [dispatch, handlers, currentViewIndex]);

  const handleClose = useCallback(() => {
    dispatch(closeImageView());
    onClose && onClose();
  }, [dispatch, onClose]);

  const handleThumbnailClick = useCallback(
    (index: number) => {
      dispatch(setCurrentViewIndex(index));
      handlers.resetZoom();
    },
    [dispatch, handlers],
  );

  // Slideshow functionality
  const { isSlideshowActive, toggleSlideshow } = useSlideshow(
    totalImages,
    handleNextImage,
  );

  // Toggle functions
  const toggleInfo = useCallback(() => {
    setShowInfo((prev) => !prev);
  }, []);

  const handleToggleFavorite = useCallback(() => {
    if (currentImage) {
      toggleFavorite(currentImage.path);
    }
  }, [currentImage, toggleFavorite]);

  // Keyboard navigation
  useKeyboardNavigation({
    onClose: handleClose,
    onNext: handleNextImage,
    onPrevious: handlePreviousImage,
    onZoomIn: handlers.handleZoomIn,
    onZoomOut: handlers.handleZoomOut,
    onRotate: handlers.handleRotate,
    onToggleInfo: toggleInfo,
  });

  // Early return if no images or invalid index
  if (!images.length || currentViewIndex === -1 || !currentImage) {
    return null;
  }

  const currentImagePath = currentImage.path;
  const currentImageAlt = `image-${currentViewIndex}`;

  return (
    <div className="fixed inset-0 z-50 mt-0 flex flex-col bg-gradient-to-b from-black/95 to-black/98 backdrop-blur-lg">
      {/* Controls */}
      <MediaViewControls
        showInfo={showInfo}
        onToggleInfo={toggleInfo}
        onToggleFavorite={handleToggleFavorite}
        isFavorite={isFavorite(currentImage.path)}
        isSlideshowActive={isSlideshowActive}
        onToggleSlideshow={toggleSlideshow}
        onClose={handleClose}
        type={type}
      />

      {/* Main viewer area */}
      <div
        className="relative flex h-full w-full items-center justify-center"
        onClick={(e) => {
          if (e.target === e.currentTarget) handleClose();
        }}
      >
        {type === 'image' && (
          <ImageViewer
            imagePath={currentImagePath}
            alt={currentImageAlt}
            scale={viewState.scale}
            position={viewState.position}
            rotation={viewState.rotation}
            isDragging={viewState.isDragging}
            onMouseDown={handlers.handleMouseDown}
            onMouseMove={handlers.handleMouseMove}
            onMouseUp={handlers.handleMouseUp}
            onMouseLeave={handlers.handleMouseUp}
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                handleClose();
              }
            }}
          />
        )}

        {/* Navigation buttons */}
        <NavigationButtons
          onPrevious={handlePreviousImage}
          onNext={handleNextImage}
        />
      </div>

      {/* Zoom controls */}
      {type === 'image' && (
        <ZoomControls
          onZoomIn={handlers.handleZoomIn}
          onZoomOut={handlers.handleZoomOut}
          onRotate={handlers.handleRotate}
          onReset={handlers.resetZoom}
          showThumbnails={showThumbnails}
        />
      )}

      {/* Thumbnails */}
      <div
        onMouseEnter={() => setShowThumbnails(true)}
        onMouseLeave={() => setShowThumbnails(false)}
      >
        <MediaThumbnails
          images={images}
          currentIndex={currentViewIndex}
          showThumbnails={showThumbnails}
          onThumbnailClick={handleThumbnailClick}
          favorites={favorites}
          type={type}
        />
      </div>

      {/* Info panel */}
      <MediaInfoPanel
        show={showInfo}
        onClose={toggleInfo}
        currentImage={currentImage}
        currentIndex={currentViewIndex}
        totalImages={totalImages}
      />
    </div>
  );
}
