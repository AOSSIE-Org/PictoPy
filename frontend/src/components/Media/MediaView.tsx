import { useState, useCallback, useMemo, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { revealItemInDir } from '@tauri-apps/plugin-opener';
import { MediaViewProps } from '@/types/Media';
import { selectCurrentViewIndex } from '@/features/imageSelectors';
import { setCurrentViewIndex, closeImageView } from '@/features/imageSlice';

// Modular components
import { MediaViewControls } from './MediaViewControls';
import { ZoomControls } from './ZoomControls';
import { MediaThumbnails } from './MediaThumbnails';
import { MediaInfoPanel } from './MediaInfoPanel';
import { ImageViewer } from './ImageViewer';
import { NavigationButtons } from './NavigationButtons';
import { ConfirmDialog } from '@/components/Dialog/ConfirmDialog';
import type { ImageViewerRef } from './ImageViewer';

// Custom hooks
import { useImageViewControls } from '@/hooks/useImageViewControls';
import { useSlideshow } from '@/hooks/useSlideshow';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';
import { useToggleFav } from '../../hooks/useToggleFav';
import { useDeleteImages } from '@/hooks/useDeleteImages';
import {
  getDeleteFromComputerPreference,
  setDeleteFromComputerPreference,
  getSkipDeleteConfirmationPreference,
  setSkipDeleteConfirmationPreference,
} from '@/hooks/useDeleteFromComputerPreference';
import { useLocation } from 'react-router';
import { ROUTES } from '@/constants/routes';

export function MediaView({
  onClose,
  type = 'image',
  images = [],
  onToggleFavorite,
}: MediaViewProps) {
  const dispatch = useDispatch();

  // Redux selectors
  const currentViewIndex = useSelector(selectCurrentViewIndex);
  const totalImages = images.length;
  // guard: images default to empty array in the signature so `images.length` is safe

  const currentImage = useMemo(() => {
    if (currentViewIndex >= 0 && currentViewIndex < images.length) {
      return images[currentViewIndex];
    }
    return null;
  }, [images, currentViewIndex]);

  const imageViewerRef = useRef<ImageViewerRef>(null);

  // Local UI state
  const [showInfo, setShowInfo] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [resetSignal, setResetSignal] = useState(0);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteFromDevice, setDeleteFromDevice] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  // Custom hooks
  const { viewState, handlers } = useImageViewControls();
  const resetViewerState = useCallback(() => {
    handlers.resetZoom();
    setResetSignal((s) => s + 1);
  }, [handlers]);

  // Navigation handlers
  const handleNextImage = useCallback(() => {
    if (currentViewIndex < images.length - 1) {
      dispatch(setCurrentViewIndex(currentViewIndex + 1));
      resetViewerState();
    }
  }, [dispatch, resetViewerState, currentViewIndex, images.length]);

  const handlePreviousImage = useCallback(() => {
    if (currentViewIndex > 0) {
      dispatch(setCurrentViewIndex(currentViewIndex - 1));
      resetViewerState();
    }
  }, [dispatch, resetViewerState, currentViewIndex]);

  const handleClose = useCallback(() => {
    dispatch(closeImageView());
    onClose && onClose();
  }, [dispatch, onClose]);

  const handleThumbnailClick = useCallback(
    (index: number) => {
      dispatch(setCurrentViewIndex(index));
      resetViewerState();
    },
    [dispatch, resetViewerState],
  );

  const location = useLocation();
  const { toggleFavourite } = useToggleFav();
  const { deleteImages } = useDeleteImages();

  /**
   * Opens the delete dialog — unless "Don't show again" was checked before,
   * in which case it deletes immediately using the Settings preference,
   * with no dialog shown at all.
   */
  const handleOpenDeleteDialog = useCallback(() => {
    if (getSkipDeleteConfirmationPreference()) {
      if (!currentImage?.id) return;
      deleteImages({
        imageIds: [currentImage.id],
        deleteFromDevice: getDeleteFromComputerPreference(),
      });
      return;
    }
    setDeleteFromDevice(getDeleteFromComputerPreference());
    setDontShowAgain(false);
    setShowDeleteDialog(true);
  }, [currentImage, deleteImages]);

  const handleConfirmDelete = useCallback(() => {
    if (!currentImage?.id) return;
    // Whatever was chosen in the dialog becomes the new default for next
    // time, independent of whether "don't show again" was also checked.
    setDeleteFromComputerPreference(deleteFromDevice);
    if (dontShowAgain) {
      setSkipDeleteConfirmationPreference(true);
    }
    deleteImages({ imageIds: [currentImage.id], deleteFromDevice });
  }, [currentImage, deleteImages, deleteFromDevice, dontShowAgain]);

  // Loop to first image handler for slideshow
  const handleLoopToStart = useCallback(() => {
    dispatch(setCurrentViewIndex(0));
    resetViewerState();
  }, [dispatch, resetViewerState]);

  // Slideshow functionality
  const { isSlideshowActive, toggleSlideshow } = useSlideshow(
    totalImages,
    handleNextImage,
    handleLoopToStart,
    currentViewIndex,
  );

  /** Opens the system file explorer at the current image's location. */
  const handleOpenFolder = async () => {
    if (!currentImage?.path) return;
    try {
      await revealItemInDir(currentImage.path);
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  };

  // Toggle functions
  const toggleInfo = useCallback(() => {
    setShowInfo((prev) => !prev);
  }, []);

  // Hooks that depend on currentImage but always declared
  const handleToggleFavourite = useCallback(() => {
    if (currentImage) {
      if (currentImage?.id) {
        // Use custom handler if provided, otherwise use default
        if (onToggleFavorite) {
          onToggleFavorite(currentImage.id);
        } else {
          toggleFavourite(currentImage.id);
        }
      }
      if (location.pathname === ROUTES.FAVOURITES) handleClose();
    }
  }, [
    currentImage,
    toggleFavourite,
    onToggleFavorite,
    location.pathname,
    handleClose,
  ]);

  const handleZoomIn = useCallback(() => {
    imageViewerRef.current?.zoomIn();
  }, []);

  const handleZoomOut = useCallback(() => {
    imageViewerRef.current?.zoomOut();
  }, []);

  const handleResetZoom = useCallback(() => {
    imageViewerRef.current?.reset();
    resetViewerState();
  }, [resetViewerState]);

  // Keyboard navigation
  useKeyboardNavigation({
    onClose: handleClose,
    onNext: handleNextImage,
    onPrevious: handlePreviousImage,
    onZoomIn: handleZoomIn,
    onZoomOut: handleZoomOut,
    onRotate: handlers.handleRotate,
    onToggleInfo: toggleInfo,
  });

  // Early return if no images or invalid index
  if (!images?.length || currentViewIndex === -1 || !currentImage) {
    return null;
  }

  // Safe variables
  const currentImagePath = currentImage.path;
  const currentImageKey = currentImage.id || currentImage.path;
  // console.log(currentImage);
  const currentImageAlt = `image-${currentViewIndex}`;
  return (
    <div className="fixed inset-0 z-50 mt-0 flex flex-col bg-linear-to-b from-white/95 to-white/98 backdrop-blur-lg dark:from-black/95 dark:to-black/98">
      {/* Controls */}
      <MediaViewControls
        showInfo={showInfo}
        onToggleInfo={toggleInfo}
        onToggleFavourite={handleToggleFavourite}
        isFavourite={currentImage.isFavourite || false}
        onOpenFolder={handleOpenFolder}
        onDelete={type === 'image' ? handleOpenDeleteDialog : undefined}
        isSlideshowActive={isSlideshowActive}
        onToggleSlideshow={toggleSlideshow}
        onClose={handleClose}
        type={type}
      />

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete photo"
        description="Remove this Photo from PictoPy"
        confirmLabel="Delete"
        onConfirm={handleConfirmDelete}
        checkboxLabel="Delete from Computer"
        checkboxChecked={deleteFromDevice}
        onCheckboxChange={setDeleteFromDevice}
        checkboxHint={
          deleteFromDevice
            ? 'The file will be permanently deleted from its folder. This cannot be undone.'
            : 'Removed from your PictoPy gallery. The file stays in its folder.'
        }
        checkboxHintDestructive={deleteFromDevice}
        dontShowAgainChecked={dontShowAgain}
        onDontShowAgainChange={setDontShowAgain}
      />

      {/* Main viewer area */}
      <div
        className="relative flex h-full w-full items-center justify-center overflow-visible"
        onClick={(e) => {
          if (e.target === e.currentTarget) handleClose();
        }}
      >
        {type === 'image' && (
          <ImageViewer
            key={currentImageKey}
            ref={imageViewerRef}
            imagePath={currentImagePath}
            alt={currentImageAlt}
            rotation={viewState.rotation}
            resetSignal={resetSignal}
          />
        )}

        {/* Navigation buttons */}
        <NavigationButtons
          onPrevious={handlePreviousImage}
          onNext={handleNextImage}
          disablePrevious={currentViewIndex <= 0}
          disableNext={currentViewIndex >= images.length - 1}
        />
      </div>

      {/* Zoom controls */}
      {type === 'image' && (
        <ZoomControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onRotate={handlers.handleRotate}
          onReset={handleResetZoom}
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
